import json
import base64

def handle(event):
    output = []
    for record in event['records']:
        json_object = record['data']
        output_record = {
            'recordId': record['recordId'],
            'result': 'Ok',
            'data': json_object
            # 'data': base64.b64encode(json.dumps(json_object).encode('utf-8')).decode('utf-8')
        }
        output.append(output_record)
    print("output: ", output)
    print("success from firehose endpoint")
    return {'records': output}
