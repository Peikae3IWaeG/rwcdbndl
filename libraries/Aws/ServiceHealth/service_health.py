from itertools import chain, product
from datetime import datetime
import requests
import yaml
from RW.Utils import parse_timedelta, csv_to_list

GLOBAL_SERVICES = [  #List from https://d3s31nlw3sm5l8.cloudfront.net/services.json
    "supportcenter",
    "marketplace",
    "chime",
    "resourcegroups",
    "organizations",
    "iam",
    "import-export",
    "interregionvpcpeering",
    "trustedadvisor",
    "route53domainregistration",
    "spencer",
    "account",
    "management-console",
    "billingconsole",
    "route53apprecoverycontroller",
    "cloudfront",
    "globalaccelerator",
    "awswaf",
    "health",
    "apipricing",
    "route53",
    "chatbot",
]


class ServiceHealth:
    def get_event_json(self, event_json_location: str) -> dict:
        url = "https://history-events-{}-prod.s3.amazonaws.com/historyevents.json".format(event_json_location)

        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "Origin": "https://health.aws.amazon.com",
            "Referer": "https://health.aws.amazon.com/",
        }
        response = requests.request("GET", url, headers=headers, timeout=10)
        if response.status_code != 200:
            raise ValueError("Incident json file not found")

        return yaml.safe_load(response.text)

    def services_filter(self, payload, within_time, regions_list, services_list, enable_global) -> list[str]:
        regions_list = csv_to_list(regions_list)
        services_list = csv_to_list(services_list)
        affected_services = list(payload)
        wanted_list = self._get_product_list(list1=regions_list, list2=services_list)
        if enable_global:
            wanted_list = self._add_global_services(wanted_list)
        type_filtered_list = self._wanted_list_qualifier(affected_services, wanted_list)
        parsed_timedelta = parse_timedelta(within_time).total_seconds()
        time_filtered_list = self._time_qualifier(type_filtered_list, payload, parsed_timedelta)
        deduplicated_list = list(set(time_filtered_list))
        return deduplicated_list

    def _get_product_list(self, list1: list[str], list2: list[str]) -> list[str]:
        products_product = product(list1, list2)
        return ["-".join([x[0], x[1]]) for x in products_product]

    def _add_global_services(self, services_list: list[str]) -> list[str]:
        return services_list + GLOBAL_SERVICES

    def _filter_time_delta(self, timestamp: str) -> int:
        now = datetime.now()
        then = datetime.fromtimestamp(int(timestamp))
        tdelta = now - then
        seconds = tdelta.total_seconds()
        return int(seconds)

    def _wanted_list_qualifier(self, services: list[str], wanted_services: list[str]) -> list[str]:
        filtered_list = []
        for service in wanted_services:
            temp = [x for x in services if service in x]
            if temp != []:
                filtered_list.append(temp)
        return list(chain.from_iterable(list(filtered_list)))

    def _time_qualifier(self, type_filtered_list: list[str], payload: dict, within_seconds: int) -> list[str]:
        time_qualified_list = []
        for service_name in type_filtered_list:
            for item in payload[service_name]:
                if self._filter_time_delta(item["date"]) < within_seconds:
                    time_qualified_list.append(service_name)
        return time_qualified_list
