import requests
from jinja2 import Environment, FileSystemLoader

def get_layer_records(url, token, where_clause):
    params = {
        'where': where_clause,
        'returnGeometry': 'false',
        'outFields': '*',
        'f': 'json',
        'token': token
    }

    response = requests.get(url, params=params)
    data = response.json()

    return data.get('features')

def create_html(records, parentglobalid, token):
    if records:
        filename = f'resultados_{parentglobalid}.html'
        env = Environment(loader=FileSystemLoader('.'))
        template = env.get_template('report_template2.html')

        layers = []
        for layer_id, layer_records in records.items():
            table_data = []
            attachments = []

            # Get field aliases for the layer
            field_aliases_url = f"{base_url}/{layer_id}?f=json&token={token}"
            field_aliases_data = requests.get(field_aliases_url).json()
            field_aliases = {field['name']: field['alias'] for field in field_aliases_data['fields']}

            for record in layer_records:
                attributes = record.get('attributes')
                for key, value in attributes.items():
                    field_alias = field_aliases.get(key, key)  # Use alias if available, otherwise use key
                    table_data.append([field_alias, str(value)])

                attachment_url = f"{base_url}/{layer_id}/{record['attributes']['objectid']}/attachments"
                attachment_data = requests.get(attachment_url, params={'f': 'json', 'token': token}).json().get('attachmentInfos', [])

                if attachment_data:
                    for attachment in attachment_data:
                        attachment_url_with_token = f"{attachment_url}/{attachment['id']}?token={token}"
                        attachments.append(attachment_url_with_token)

            layers.append({
                'layer_id': layer_id,
                'table_data': table_data,
                'attachments': attachments
            })

        with open(filename, 'w') as f:
            f.write(template.render(layers=layers, parentglobalid=parentglobalid))

        print(f'Se ha generado el HTML: {filename}')
    else:
        print(f'No se encontraron registros para parentglobalid: {parentglobalid}')




base_url = 'https://services6.arcgis.com/kyerLIHvrND0OSya/arcgis/rest/services/service_050fd5776aea42baa2d4c8fdf1b65aeb/FeatureServer'
username = 'SINC_Campo_INVIAS'
password = 'SINC_Campo2022'

token_url = 'https://www.arcgis.com/sharing/rest/generateToken'
token_params = {
    'username': username,
    'password': password,
    'referer': 'https://www.arcgis.com',
    'f': 'json'
}

token_response = requests.post(token_url, data=token_params)
token = token_response.json().get('token')

if token:
    parentglobalid = input('Ingrese el parentglobalid: ')
    records = {}

    for layer_id in range(18):
        url = f'{base_url}/{layer_id}/query'
        where_clause = f"globalid = '{parentglobalid}'" if layer_id == 0 else f"parentglobalid = '{parentglobalid}'"

        layer_records = get_layer_records(url, token, where_clause)
        if layer_records:
            records[layer_id] = layer_records

    create_html(records, parentglobalid, token)
else:
    print('Error al generar el token.')
