import logging
from flask import Flask, request, jsonify
import mysql.connector
from datetime import datetime
import time
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

# Configure the logging module
logging.basicConfig(format='%(asctime)s|%(name)s|%(levelname)s|%(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)
logger = logging.getLogger(__name__)

# Database Configuration
db_config = {
    "host": "127.0.0.1",
    "user": "opsuser",
    "password": "opsuser@6Dtech",
    "database": "OPS",
    "pool_size": 5  # Adjust the pool size based on your requirements
}

logger.info(f"Connecting to database with configuration: {db_config}")

# Database Connection Pool
db_pool = mysql.connector.pooling.MySQLConnectionPool(**db_config)

def execute_query(query, params=None, fetch=True):
    try:
        connection = db_pool.get_connection()
        with connection.cursor(dictionary=True) as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            # Commit only for INSERT and UPDATE queries
            if query.lower().startswith("insert") or query.lower().startswith("update"):
                connection.commit()

                # Return None for INSERT queries to avoid fetching results
                if query.lower().startswith("insert"):
                    return None

            # Fetch results only if explicitly requested
            result = cursor.fetchall() if fetch else None

        return result
    except Exception as e:
        logger.error(f"Error executing query: {query}. Params: {params}. Error: {e}")
        raise e
    finally:
        connection.close()

def insert_host(hostname, host_ip, host_os):
    insert_host_query = "INSERT INTO host_master (hostname, ip, host_os) VALUES (%s, %s, %s)"
    insert_host_params = (hostname, host_ip, host_os)
    execute_query(insert_host_query, insert_host_params)
    logger.debug(f"Inserted host into host_master for Hostname {hostname}")

def update_host_status(host_id, host_uptime, request_time):
    update_host_status_query = "UPDATE host_status SET uptime = %s, last_updated_date = %s, RequestDate = %s WHERE host_master_id = %s"
    update_host_status_params = (host_uptime, datetime.now(), request_time, host_id)
    execute_query(update_host_status_query, update_host_status_params, fetch=False)
    logger.debug(f"Updated host_status for HostID {host_id}")

def insert_host_status(host_id, host_uptime, request_time):
    insert_host_status_query = "INSERT INTO host_status (host_master_id, uptime, last_updated_date, RequestDate) VALUES (%s, %s, %s, %s)"
    insert_host_status_params = (host_id, host_uptime, datetime.now(), request_time)
    execute_query(insert_host_status_query, insert_host_status_params, fetch=False)
    logger.debug(f"Inserted host_status for HostID {host_id}")

def insert_service(kpi_name, kpi_sub_type):
    insert_service_query = "INSERT INTO services_master (service_name, service_sub_type) VALUES (%s, %s)"
    insert_service_params = (kpi_name, kpi_sub_type)
    execute_query(insert_service_query, insert_service_params)
    logger.debug(f"Inserted service for KpiName {kpi_name}")

def get_service_id(kpi_name):
    service_id_query = "SELECT id FROM services_master WHERE service_name = %s"
    service_id_params = (kpi_name,)
    service_id_result = execute_query(service_id_query, service_id_params)
    return service_id_result[0]["id"] if service_id_result else None

def process_services_and_keys(data, host_id, request_id, request_time):
    # Processing logic for services and keys
    for kpi in data["Kpis"]:
        service_name = kpi["KpiName"]
        service_sub_type = kpi["KpiSubType"]

        # Check if the service exists in services_master table
        existing_service = execute_query("SELECT * FROM services_master WHERE service_name = %s", (service_name,))

        if not existing_service:
            # Insert into services_master if not present
            insert_service(service_name, service_sub_type)

        # Get the service_id for the current service
        service_id = get_service_id(service_name)

        for key in kpi["Keys"]:
            key_name = key["KeyName"]

            # Check if the key exists in services_details table
            existing_key = execute_query("SELECT * FROM services_details WHERE service_id = %s AND service_key_name = %s", (service_id, key_name))

            if not existing_key:
                # Insert into services_details if not present
                threshold_value = 80.0 if service_sub_type == "P" else 0 if service_sub_type == "B" else 1000
                insert_key_query = "INSERT INTO services_details (service_id, service_key_name, threshold_value, severity) VALUES (%s, %s, %s, %s)"
                insert_key_params = (service_id, key_name, threshold_value, "s3")
                execute_query(insert_key_query, insert_key_params)
                logger.debug(f"Inserted key for KeyName {key_name}")

            # Check if the service is available in service_status table
            status_query = "SELECT * FROM service_status WHERE service_id = %s AND service_key_name = %s"
            status_params = (service_id, key_name)
            existing_status = execute_query(status_query, status_params)

            # Initialize last_service_key_value here
            last_service_key_value = None

            if not existing_status:
                # Check if the key exists in services_details table
                key_query = "SELECT * FROM services_details WHERE service_id = %s AND service_key_name = %s"
                key_params = (service_id, key_name)
                existing_key = execute_query(key_query, key_params)

                # Get the last_service_key_value for the current key
                last_service_key_value_query = "SELECT service_key_value FROM service_status WHERE host_id = %s AND service_id = %s AND service_key_name = %s ORDER BY last_updated_date DESC LIMIT 1"
                last_service_key_value_params = (host_id, service_id, key_name)
                last_service_key_value_result = execute_query(last_service_key_value_query, last_service_key_value_params)

                if last_service_key_value_result:
                    last_service_key_value = last_service_key_value_result[0]["service_key_value"]

                insert_status_query = "INSERT INTO service_status (host_id, service_id, service_details_id, service_key_name, service_key_value, service_key_desc, last_updated_date, alert_gen_flag, last_service_key_value, RequestDate) VALUES (%s, %s, %s, %s, %s, %s, %s, 1, %s, %s)"
                if existing_key:
                    insert_status_params = (host_id, service_id, existing_key[0]["id"], key_name, key["KeyValue"], key["KeyDesc"], datetime.now(), last_service_key_value, request_time)
                else:
                    insert_status_params = (host_id, service_id, None, key_name, key["KeyValue"], key["KeyDesc"], datetime.now(), last_service_key_value, request_time)

                execute_query(insert_status_query, insert_status_params)
                logger.debug(f"Inserted status for KeyName {key_name}")
            else:
                # Update last_service_key_value within the else block
                last_service_key_value = existing_status[0]["last_service_key_value"]

                # Get the last_service_key_value for the current key
                last_service_key_value_query = "SELECT service_key_value FROM service_status WHERE host_id = %s AND service_id = %s AND service_key_name = %s ORDER BY last_updated_date DESC LIMIT 1"
                last_service_key_value_params = (host_id, service_id, key_name)
                last_service_key_value_result = execute_query(last_service_key_value_query, last_service_key_value_params)

                if last_service_key_value_result:
                    last_service_key_value = last_service_key_value_result[0]["service_key_value"]

                update_status_query = "UPDATE service_status SET service_key_value = %s, service_key_desc = %s, last_updated_date = %s, alert_gen_flag = 1, last_service_key_value = %s, RequestDate = %s WHERE host_id = %s AND service_id = %s AND service_key_name = %s"
                update_status_params = (key["KeyValue"], key["KeyDesc"], datetime.now(), last_service_key_value if last_service_key_value is not None else key["KeyValue"], request_time, host_id, service_id, key_name)
                execute_query(update_status_query, update_status_params, fetch=False)  # Set fetch=False for UPDATE queries
                logger.debug(f"Updated status for KeyName {key_name}")

            # Insert into alert_history table
            insert_alert_query = "INSERT INTO alert_history (RequestId, RequestDate, host_id, service_id, service_details_id, service_key_name, service_key_value, service_key_desc, updated_date, Month_Partition, Is_Status_Changed) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

            if existing_key:
                insert_alert_params = (request_id, request_time, host_id, service_id, existing_key[0]["id"], key_name, key["KeyValue"], key["KeyDesc"], datetime.now(), request_time.strftime("%m"), 0)
            else:
                insert_alert_params = (request_id, request_time, host_id, service_id, None, key_name, key["KeyValue"], key["KeyDesc"], datetime.now(), request_time.strftime("%m"), 0)

            # Check if the service_key_value and last_service_key_value are different
            status_difference_query = "SELECT service_key_value, last_service_key_value FROM service_status WHERE host_id = %s AND service_id = %s AND service_details_id = %s AND service_key_name = %s ORDER BY last_updated_date DESC LIMIT 1"
            status_difference_params = (host_id, service_id, insert_alert_params[4], key_name)
            status_difference_result = execute_query(status_difference_query, status_difference_params)

            if status_difference_result and status_difference_result[0]["service_key_value"] != status_difference_result[0]["last_service_key_value"]:
                insert_alert_params = (*insert_alert_params[:-1], 1)  # Set Is_Status_Changed to 1
            else:
                insert_alert_params = (*insert_alert_params[:-1], 0)  # Set Is_Status_Changed to 0

            execute_query(insert_alert_query, insert_alert_params, fetch=False)  # Set fetch=False for INSERT queries
            logger.debug(f"Inserted into alert_history for KeyName {key_name}")

def parallel_processing_steps(data, host_id, request_id, request_time):
    with ThreadPoolExecutor(max_workers=3) as executor:
        # Submit processing functions to the thread pool
        executor.submit(process_services_and_keys, data, host_id, request_id, request_time)

# API route to handle KPI stats submission
@app.route('/kpi_stats_submit', methods=['POST'])
def kpi_stats_submit():
    start_time = time.time()
    try:
        data = request.get_json()
        logger.info(f"Received JSON data: {data}")

        # Check and insert into host_master table
        hostname = data.get("Hostname")
        host_os = data.get("HostOS")
        host_ip = data.get("HostIP")
        request_id = data.get("RequestId")
        request_time = datetime.strptime(data.get("RequestTime"), "%Y-%m-%d %H:%M:%S")

        existing_host = execute_query("SELECT * FROM host_master WHERE hostname = %s", (hostname,))
        host_id_result = execute_query("SELECT id FROM host_master WHERE hostname = %s", (hostname,))

        if not existing_host:
            # Insert into host_master if not present
            insert_host(hostname, host_ip, host_os)

        host_id = host_id_result[0]["id"] if host_id_result and host_id_result[0] else None

        existing_host_status = execute_query("SELECT * FROM host_status WHERE host_master_id = %s", (host_id,))

        if existing_host_status:
            # Update the entry in host_status table
            update_host_status(host_id, data.get("Host_uptime"), request_time)
        else:
            # Insert a new entry in host_status table
            insert_host_status(host_id, data.get("Host_uptime"), request_time)

        # Parallelize processing for KPIs, services, and keys
        parallel_processing_steps(data, host_id, request_id, request_time)

        processing_time = time.time() - start_time
        logger.info(f"Processing time for request- {request_id} : {processing_time} seconds")
        return jsonify({"message": "KPI stats submitted successfully"}), 200

    except Exception as e:
        logger.error(f"Error in kpi_stats_submit: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5070)