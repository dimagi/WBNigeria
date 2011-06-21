# put in separate file because the two places
# they're needed import each other
# adherence query types
QUERY_TYPE_SMS = 1
QUERY_TYPE_IVR = 2
QUERY_TYPES = (
    (QUERY_TYPE_SMS, 'SMS'),
    (QUERY_TYPE_IVR, 'IVR'),
    )

ADHERENCE_SOURCE_SMS = 1
ADHERENCE_SOURCE_IVR = 2
ADHERENCE_SOURCE_WISEPILL = 3
ADHERENCE_SOURCE = (
    (ADHERENCE_SOURCE_SMS, "SMS"),
    (ADHERENCE_SOURCE_IVR, "IVR"),
    (ADHERENCE_SOURCE_WISEPILL, "Wisepill"),
    )

