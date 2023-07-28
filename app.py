import json
import shutil
import tempfile
import zipfile
from datetime import datetime
import os
import requests
from flask import Flask, render_template, request, jsonify, make_response, send_file, url_for
from flask_session import Session
from jinja2 import Environment, FileSystemLoader

app = Flask(__name__, static_folder='static')
app.config['JSON_AS_ASCII'] = False
app.config['SECRET_KEY'] = '0527'

base_url = 'https://services6.arcgis.com/kyerLIHvrND0OSya/arcgis/rest/services/service_050fd5776aea42baa2d4c8fdf1b65aeb/FeatureServer'
username = 'xxxxxx'
password = 'xxxxxx'

# Configurar Flask-Session
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True

Session(app)


def get_token():
    token_url = 'https://www.arcgis.com/sharing/rest/generateToken'
    token_params = {
        'username': username,
        'password': password,
        'referer': 'https://www.arcgis.com',
        'f': 'json'
    }

    token_response = requests.post(token_url, data=token_params)
    token = token_response.json().get('token')

    return token


def get_layer_names(token):
    params = {
        'f': 'json',
        'token': token
    }

    response = requests.get(base_url, params=params)
    data = response.json()

    return {layer['id']: layer['name'] for layer in data.get('layers', [])}


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


def search_globalids(search_str, searchDeptoStr, searchMpioStr, searchVeredaStr, searchOrgStr, token=None, layer_id=0):


    token = get_token()
    url = f'{base_url}/{layer_id}/query'

    where_clause = []

    if searchOrgStr:
        where_clause.append(f"UPPER(organizacion) = UPPER('{searchOrgStr}')")  # Use exact match for organization

    if search_str:
        search_fields = [
            "organizacion",
            "subOrganizacion",
            "nombreDepartamento",
            "codigoDepartamento",
            "nombreMunicipio",
            "codigoMunicipio",
            "nombreVereda",
            "codigoVereda",
            "nombreVeredaLibre",
            "codigoVia",
            "nombreVia",
            "nombreRecolector",
            "direccionTerritorial",
            "cargoRecolector",
            "nombreDelegado",
        ]
        where_clause.append(" OR ".join(f"UPPER({field}) LIKE UPPER('%{search_str}%')" for field in search_fields))

    if searchDeptoStr:
        where_clause.append(f"nombreDepartamento = '{searchDeptoStr}'")

    if searchMpioStr:
        where_clause.append(f"nombreMunicipio = '{searchMpioStr}'")

    if searchVeredaStr:
        where_clause.append(f"nombreVereda = '{searchVeredaStr}'")

    where_clause_str = ' AND '.join(where_clause)

    if not where_clause_str:
        where_clause_str = '1=1'

    params = {
        'where': where_clause_str,
        'returnGeometry': 'false',
        'outFields': '*',
        'f': 'json',
        'token': token
    }

    response = requests.get(url, params=params)
    data = response.json()

    return [{"id": record['attributes']['globalid'], "name": record['attributes']['nombreVia']} for record in data.get('features')]



def search_globalids_org(searchOrgStr, token, layer_id=0):
    url = f'{base_url}/{layer_id}/query'

    where_clause = []

    if searchOrgStr:
        where_clause.append(f"organizacion = '{searchOrgStr}'")

    where_clause_str = ' AND '.join(where_clause)

    if not where_clause_str:
        where_clause_str = '1=1'

    params = {
        'where': where_clause_str,
        'returnGeometry': 'false',
        'outFields': 'globalid, nombreVia',
        'f': 'json',
        'token': token
    }

    response = requests.get(url, params=params)
    data = response.json()

    return [{"id": record['attributes']['globalid'], "name": record['attributes']['nombreVia']} for record in data.get('features')]



def create_html(records, parentglobalid, token, layer_names):
    if records:
        env = Environment(loader=FileSystemLoader('.'))
        template = env.get_template('templates/report_template2.html')

        layers = []
        via_name = ""

        for layer_id, layer_records in records.items():
            layer_data = []

            field_aliases_url = f"{base_url}/{layer_id}?f=json&token={token}"
            field_aliases_data = requests.get(field_aliases_url).json()
            field_aliases = {field['name']: field['alias'] for field in field_aliases_data['fields']}

            field_aliases['inventarioPropiedades'] = 'Inventario Propiedades'
            field_aliases['invSitioCritico'] = 'Inventario Sitio Crítico'
            field_aliases['invObraDrenaje'] = 'Inventario Obra Drenaje'
            field_aliases['invPuentes'] = 'Inventario Puentes'
            field_aliases['mejoraPlacaHuella'] = 'Mejora Placa Huella'
            field_aliases['mejoraObrasDrenaje'] = 'Mejora Obra Drenaje'
            field_aliases['invMuros'] = 'Inventario Muros'
            field_aliases['mantRoceria'] = 'Mantenimiento Rocería'
            field_aliases['mantBacheo'] = 'Mantenimiento Bacheo'
            field_aliases['mantRemocionDerrumbes'] = 'Mantenimiento Remoción Derrumbes'
            field_aliases['mantReconsZanjasCorona'] = 'Mantenimiento Reconstruccion Zanjas Corona'
            field_aliases['mantReparacionSenales'] = 'Mantenimiento Reparacionales'
            field_aliases['mejoraConstruccionBateas'] = 'Mejora Construcción Bateas'
            field_aliases['mejoraObraIngVerde'] = 'Mejora Obra Ing Verde'
            field_aliases['mejoraInstalacionSenales'] = 'Mejora Instlación Señales'
            field_aliases['mejoraObrasEstabilizacion'] = 'Mejora Obra Estabilización'
            field_aliases['mejoraPuentePonton'] = 'Mejora Puente Pontón'
            field_aliases['abscisaFinal'] = 'Abscisa Final'

            for record in layer_records:
                attributes = record.get('attributes')
                table_data = []
                attachments = []

                for key, value in attributes.items():
                    if layer_id == 0 and key == "nombreVia":
                        via_name = value
                    if key == "parentglobalid":
                        value = via_name
                    field_alias = field_aliases.get(key, key)
                    if key not in ["globalid", "objectid"]:
                        if key in ["EditDate", "CreationDate", "fecha"] and value is not None:
                            value = datetime.fromtimestamp(value / 1000).strftime('%Y-%m-%d %H:%M:%S')
                        table_data.append([field_alias, "" if value is None else str(value)])

                attachment_url = f"{base_url}/{layer_id}/{record['attributes']['objectid']}/attachments"
                attachment_data = requests.get(attachment_url, params={'f': 'json', 'token': token}).json().get(
                    'attachmentInfos', [])

                if attachment_data:
                    for attachment in attachment_data:
                        attachment_url_with_token = f"{attachment_url}/{attachment['id']}?token={token}"
                        attachments.append(attachment_url_with_token)

                layer_data.append((record['attributes']['objectid'], table_data, attachments))

            layers.append({
                'layer_title': layer_names.get(layer_id, f'Layer {layer_id}'),
                'data': layer_data
            })

        html_content = template.render(layers=layers, parentglobalid=parentglobalid, via_name=via_name)

        return html_content
    else:
        return None

@app.route('/')
def index():
    departamentos = get_departamentos()
    organizaciones = get_organizaciones()
    return render_template('index.html', departamentos=departamentos, organizaciones=organizaciones)

@app.route('/update_filters', methods=['POST'])
def update_filters():
    selected_depto = request.form.get('selected_depto')
    selected_mpio = request.form.get('selected_mpio')
    selected_vereda = request.form.get('selected_vereda')
    selected_org = request.form.get('selected_org')
    
    token = get_token()
    
    filter_dict = {
        'nombreDepartamento': selected_depto,
        'nombreMunicipio': selected_mpio,
        'nombreVereda': selected_vereda,
        'organizacion': selected_org
    }
    
    departamentos = get_unique_values(token, 'nombreDepartamento', filter_dict)
    municipios = get_unique_values(token, 'nombreMunicipio', filter_dict)
    veredas = get_unique_values(token, 'nombreVereda', filter_dict)
    organizaciones = get_unique_values(token, 'organizacion', filter_dict)
    
    response_data = {
        'departamentos': departamentos,
        'municipios': municipios,
        'veredas': veredas,
        'organizaciones': organizaciones
    }
    
    return jsonify(response_data)


def get_unique_values(field, filters=None):
    token = get_token()
    if token:
        where_clause = generate_where_clause(filters)
        params = create_query_params(where_clause, field, token)
        response = requests.get(f'{base_url}/0/query', params=params)
        data = response.json()
        unique_values = list(set([record['attributes'][field] for record in data.get('features', [])]))
        return unique_values
    return []

def generate_where_clause(filters):
    where_clause = []
    if filters:
        for key, value in filters.items():
            if value is not None:
                where_clause.append(f"{key} = '{value}'")
    where_clause_str = ' AND '.join(where_clause)
    return where_clause_str if where_clause_str else '1=1'


def get_departamentos():
    token = get_token()

    if token:
        url = f'{base_url}/0/query'
        params = {
            'where': '1=1',
            'returnGeometry': 'false',
            'outFields': 'nombreDepartamento',
            'f': 'json',
            'token': token
        }

        response = requests.get(url, params=params)
        data = response.json()

        departamentos = list(set([record['attributes']['nombreDepartamento'] for record in data.get('features', [])]))
        return departamentos

    return []


@app.route('/get_municipios', methods=['POST'])
def get_municipios():
    selected_depto = request.form.get('selected_depto')
    token = get_token()

    if token and selected_depto:
        url = f'{base_url}/0/query'
        params = {
            'where': f"nombreDepartamento = '{selected_depto}'",
            'returnGeometry': 'false',
            'outFields': 'nombreMunicipio',
            'f': 'json',
            'token': token
        }

        response = requests.get(url, params=params)
        data = response.json()

        municipios = list(set([record['attributes']['nombreMunicipio'] for record in data.get('features', [])]))
        return jsonify({'municipios': municipios})

    return jsonify({'municipios': []})


@app.route('/get_veredas', methods=['POST'])
def get_veredas():
    selected_mpio = request.form.get('selected_mpio')
    token = get_token()

    if token and selected_mpio:
        url = f'{base_url}/0/query'
        params = {
            'where': f"nombreMunicipio = '{selected_mpio}'",
            'returnGeometry': 'false',
            'outFields': 'nombreVereda',
            'f': 'json',
            'token': token
        }

        response = requests.get(url, params=params)
        data = response.json()

        veredas = list(set([record['attributes']['nombreVereda'] for record in data.get('features', [])]))
        return jsonify({'veredas': veredas})

    return jsonify({'veredas': []})


@app.route('/get_municipios_veredas', methods=['POST'])
def get_municipios_veredas():
    selected_depto = request.form.get('selected_depto')
    token = get_token()

    if token:
        url = f'{base_url}/0/query'

        where_clause = []
        if selected_depto:
            where_clause.append(f"nombreDepartamento = '{selected_depto}'")

        where_clause_str = ' OR '.join(where_clause)
        if not where_clause_str:
            where_clause_str = '1=1'

        params = {
            'where': where_clause_str,
            'returnGeometry': 'false',
            'outFields': 'nombreMunicipio, nombreVereda',
            'f': 'json',
            'token': token
        }

        response = requests.get(url, params=params)
        data = response.json()

        municipios = list(set([record['attributes']['nombreMunicipio'] for record in data.get('features', [])]))
        veredas = list(set([record['attributes']['nombreVereda'] for record in data.get('features', [])]))

        response_data = {'municipios': municipios, 'veredas': veredas}
        return jsonify(response_data)


@app.route('/get_organizaciones', methods=['POST'])
def get_organizaciones():
    selected_depto = request.form.get('selected_depto')
    selected_mpio = request.form.get('selected_mpio')
    selected_vereda = request.form.get('selected_vereda')
    token = get_token()  # Assuming you have implemented the 'get_token' function

    if token:
        url = f'{base_url}/0/query'

        where_clause = []
        if selected_depto:
            where_clause.append(f"nombreDepartamento = '{selected_depto}'")
        if selected_mpio:
            where_clause.append(f"nombreMunicipio = '{selected_mpio}'")
        if selected_vereda:
            where_clause.append(f"nombreVereda = '{selected_vereda}'")

        where_clause_str = ' OR '.join(where_clause)
        if not where_clause_str:
            where_clause_str = '1=1'

        params = {
            'where': where_clause_str,
            'returnGeometry': 'false',
            'outFields': 'organizacion',
            'f': 'json',
            'token': token
        }

        response = requests.get(url, params=params)
        data = response.json()

        organizaciones = list(set([record['attributes']['organizacion'] for record in data.get('features', [])]))

        response_data = {'organizaciones': organizaciones}
        return jsonify(response_data)

    return jsonify({'organizaciones': []})

def capitalize_words(input_str):
    return ' '.join(word.capitalize() for word in input_str.split())

@app.route('/generate_report', methods=['POST'])
def generate_report():
    search_str = request.form.get('searchStr')
    searchDeptoStr = request.form.get('searchDeptoStr')
    searchMpioStr = request.form.get('searchMpioStr')
    searchVeredaStr = request.form.get('searchVeredaStr')
    searchOrgStr = request.form.get('searchOrgStr')

    if not search_str and not searchDeptoStr and not searchMpioStr and not searchVeredaStr and not searchOrgStr:
        return jsonify({'error': 'Por favor, ingrese al menos un criterio de búsqueda.'})

    token = get_token()

    if token:
        layer_names = get_layer_names(token)
        if searchOrgStr:
            globalids = search_globalids_org(searchOrgStr, token=token)
        else:
            globalids = search_globalids(search_str, searchDeptoStr, searchMpioStr, searchVeredaStr, searchOrgStr, token=token)

        if globalids:
            formatted_globalids = [{"id": record['id'], "name": capitalize_words(record['name'])} for record in globalids]
            results = {'globalids': formatted_globalids}
            response = jsonify(results)
            response.set_cookie('searchStr', search_str)
            return response
        else:
            return jsonify({'error': 'No se encontraron coincidencias para los criterios de búsqueda proporcionados.'})

    return jsonify({'error': 'Error al generar el token.'})




@app.route('/generate_selected_report', methods=['GET'])
def generate_selected_report():
    selected_globalid = request.args.get('selected_globalid')
    token = get_token()

    if token:
        layer_names = get_layer_names(token)
        parentglobalid = selected_globalid

        records = {}

        for layer_id in range(18):
            url = f'{base_url}/{layer_id}/query'
            where_clause = f"globalid = '{selected_globalid}'" if layer_id == 0 else f"parentglobalid = '{selected_globalid}'"

            layer_records = get_layer_records(url, token, where_clause)
            if layer_records:
                records[layer_id] = layer_records

        filename = f'report_{parentglobalid}.html'

        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                html_content = f.read()
            return html_content

        html_content = create_html(records, selected_globalid, token, layer_names)
        if html_content:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)

            response = make_response(html_content)
            response.headers['Content-Disposition'] = f'attachment; filename={filename}'
            response.headers['Content-Type'] = 'text/html'
            return response

    return jsonify({'error': 'Error generating token.'})


@app.route('/generate_all_reports', methods=['POST'])
def generate_all_reports():
    search_str = request.form.get('searchStr')
    searchDeptoStr = request.form.get('searchDeptoStr')
    searchMpioStr = request.form.get('searchMpioStr')
    searchVeredaStr = request.form.get('searchVeredaStr')  # Agregar esta línea
    searchOrgStr = request.form.get('searchOrgStr')        # Agregar esta línea

    token = get_token()

    if token:
        layer_names = get_layer_names(token)
        globalids = search_globalids(search_str, searchDeptoStr, searchMpioStr, searchVeredaStr, searchOrgStr)  # Modificar esta línea

        if globalids:
            temp_dir = tempfile.mkdtemp()  # Directorio temporal para guardar los informes

            html_files = []  # Lista para almacenar los nombres de los archivos HTML generados

            for globalid in globalids:
                selected_globalid = globalid['id']
                parentglobalid = selected_globalid

                records = {}

                for layer_id in range(18):
                    url = f'{base_url}/{layer_id}/query'
                    where_clause = f"globalid = '{selected_globalid}'" if layer_id == 0 else f"parentglobalid = '{selected_globalid}'"

                    layer_records = get_layer_records(url, token, where_clause)
                    if layer_records:
                        records[layer_id] = layer_records

                via_name = globalid['name']
                filename = f'report_{via_name}.html'
                filepath = os.path.join(temp_dir, filename)

                if not os.path.exists(filepath):
                    html_content = create_html(records, selected_globalid, token, layer_names)
                    if html_content:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(html_content)
                        html_files.append((filepath, via_name))  # Agregar la ruta del archivo HTML a la lista html_files
                else:
                    print(f'El archivo ya existe: {filename}')

            # Crear un archivo ZIP con todos los informes generados
            zip_filepath = os.path.join(temp_dir, 'informes.zip')
            with zipfile.ZipFile(zip_filepath, 'w') as zip_file:
                for file, via_name in html_files:
                    zip_file.write(file, f'report_{via_name}.html')

            # Eliminar los archivos HTML individuales
            for file, _ in html_files:
                os.remove(file)

            # Mover el archivo ZIP a la ubicación correcta
            destination = os.path.join(os.getcwd(), 'static', 'informes.zip')
            shutil.move(zip_filepath, destination)

            # Obtener la URL de descarga del archivo ZIP
            download_url = url_for('static', filename='informes.zip')

            # Devolver la URL de descarga en la respuesta JSON
            return jsonify({'download_url': download_url})

        else:
            return jsonify({'error': f'No se encontraron coincidencias para: {search_str}'})

    return jsonify({'error': 'Error al generar el token.'})



@app.route('/download_all_reports', methods=['GET'])
def download_all_reports():
    try:
        filename = request.args.get('filename')

        if filename:
            # Obtener la ruta completa del archivo ZIP
            zip_filepath = os.path.join(os.getcwd(), filename)

            # Crear la respuesta y establecer el encabezado Content-Disposition
            response = make_response(send_file(zip_filepath, as_attachment=True))
            response.headers['Content-Disposition'] = f'attachment; filename={filename}'

            return response

    except Exception as e:
        print(f'Error al descargar todos los informes: {e}')

    return jsonify({'error': 'Error al descargar todos los informes.'})


if __name__ == '__main__':
    app.run()