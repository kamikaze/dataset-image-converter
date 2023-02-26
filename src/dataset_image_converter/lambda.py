import sys


def handler(event, context):
    print(event)
    return f'Hello from AWS Lambda using Python {sys.version} !'
