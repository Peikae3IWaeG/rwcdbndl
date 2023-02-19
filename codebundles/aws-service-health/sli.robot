*** Settings ***
Metadata          Author     JD
Documentation     This codebundle sets up a monitor for a specific region and AWS Product, which is then periodically checked for
...               ongoing incidents based on the history available at https://history-events-eu-west-1-prod.s3.amazonaws.com/historyevents.json.
Force Tags        AWS    Status    Health    services    Up    Available    Platform    Amazon    Cloud    Incidents
Library    RW.Core
Library    Aws.ServiceHealth
*** Tasks ***
Get Number of AWS Incidents Effecting My Workspace

   RW.Core.Import User Variable    WITHIN_TIME
   ...    type=string
   ...    pattern=((\d+?)d)?((\d+?)h)?((\d+?)m)?((\d+?)s)?
   ...    description=How far back in incident history to check, in the format "1d1h15m", with possible unit values being 'd' representing days, 'h' representing hours, 'm' representing minutes, and 's' representing seconds.
   ...    example=30m
   ...    default=15m
   RW.Core.Import User Variable    PRODUCTS
   ...    type=string
   ...    description=Which product(s) to monitor for incidents. Accepts CSV. For further examples refer to the product names at https://d3s31nlw3sm5l8.cloudfront.net/services.json
   ...    pattern=\w*
   ...    default=ec2
   ...    example=sns,eks,ecs
   RW.Core.Import User Variable    REGIONS
   ...    type=string
   ...    description=Which region to monitor for incidents. Accepts CSV. For further region value examples refer to regions at https://d3s31nlw3sm5l8.cloudfront.net/services.json or use `aws ec2 describe-regions --query 'Regions[*].RegionName'` command.
   ...    pattern=\w*
   ...    default=us-east-1
   ...    example=us-west-1,eu-west-2
   RW.Core.Import User Variable    INCLUDE_GLOBAL
   ...    type=bool
   ...    description=Monitor all non-regional AWS services as well
   ...    pattern=\w*
   ...    default=true
   RW.Core.Import User Variable    INCIDENTS_JSON_BUCKET_LOCATION
    ...    type=string
    ...    description=Set a region for S3 bucket containing incidents info. Only regions listed in the dropdown menu are supported.
    ...    pattern=\w*
    ...    enum=[ap-northeast-1, eu-west-1, us-east-1, us-west-2] 
    ...    default=us-east-1

    ${history}=    Aws.ServiceHealth.get_event_json    ${INCIDENTS_JSON_BUCKET_LOCATION}
    ${filtered}=    Aws.ServiceHealth.services_filter    ${history}    ${WITHIN_TIME}    ${PRODUCTS}    ${REGIONS}    ${INCLUDE_GLOBAL}

    Log    ${filtered}
    ${metric}=    Evaluate    len($filtered)
    Log    count: ${metric}
    RW.Core.Push Metric    ${metric}
