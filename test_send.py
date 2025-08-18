
import requests

POST_STATE = "http://192.168.10.40:1888/poststate";
header_key = "apiKey"
header_value = "pdcAPI"
POST_STATE_ON = True

try:
    assign_data = {
        "message": "Success Pick Up",
        "data": {
                "lot_no": "Y5205014TL27",
                "status": "R",
                "from_stocker": "",
                "from_level": "",
                "from_block": "",
                "to_stocker": "AM_BURN_S_0002",
                "to_level": "1",
                "to_block": "4",
                "assigned_to": "SDT_001",
               "job_no": "5"
            }
        }

    assign_destination_url = POST_STATE  # เปลี่ยนเป็น URL จริง
    headers = {
        header_key: header_value
    }
    if(POST_STATE_ON):
        response = requests.post(assign_destination_url, json=assign_data, headers=headers)
        print(response)
except Exception as e:
    pass