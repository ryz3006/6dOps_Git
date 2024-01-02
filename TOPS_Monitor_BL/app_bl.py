import logging
from flask import Flask, request, jsonify
import mysql.connector
from datetime import datetime

app = Flask(__name__)

# Configure the logging module
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Database Configuration
db_config = {
    "host": "127.0.0.1",
    "user": "opsuser",
    "password": "opsuser@6Dtech",
    "database": "OPS"
}

logger.info(f"Connecting to database with configuration: {db_config}")

# Helper function to execute SQL queries
def execute_query(query, params=None, fetch=True):
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        # Commit only for INSERT and UPDATE queries
        if query.lower().startswith("insert") or query.lower().startswith("update"):
            connection.commit()

        # Fetch results only if explicitly requested
        result = cursor.fetchall() if fetch else None

        connection.close()
        return result
    except Exception as e:
        logger.error(f"Error executing query: {query}. Params: {params}. Error: {e}")
        raise e

# API route to handle KPI stats submission
@app.route('/kpi_stats_submit', methods=['POST'])
def kpi_stats_submit():
    try:
        data = request.get_json()
        logger.info(f"Received JSON data: {data}")

        # Check and insert into host_master table
        hostname = data.get("Hostname")
        host_os = data.get("HostOS")
        host_ip = data.get("HostIP")

        # Extract RequestId and RequestTime from JSON
        request_id = data.get("RequestId")
        request_time = datetime.strptime(data.get("RequestTime"), "%Y-%m-%d %H:%M:%S")


        # Check if the host exists in host_master table
        host_query = "SELECT * FROM host_master WHERE hostname = %s"
        host_params = (hostname,)
        existing_host = execute_query(host_query, host_params)

        if not existing_host:
            # Insert into host_master if not present
            insert_host_query = "INSERT INTO host_master (hostname, ip, host_os) VALUES (%s, %s, %s)"
            insert_host_params = (hostname, host_ip, host_os)
            execute_query(insert_host_query, insert_host_params)
            logger.info(f"Inserted host into host_master for Hostname {hostname}")

       # Continue processing for host_status table
        host_query = "SELECT id FROM host_master WHERE hostname = %s"
        host_params = (hostname,)
        host_id_result = execute_query(host_query, host_params)
        host_id = host_id_result[0]["id"] if host_id_result else None

        # Check if the host exists in host_status table
        host_status_query = "SELECT * FROM host_status WHERE host_master_id = %s"
        host_status_params = (host_id,)
        existing_host_status = execute_query(host_status_query, host_status_params)

        if existing_host_status:
            # Update the entry in host_status table
            update_host_status_query = "UPDATE host_status SET uptime = %s, last_updated_date = %s, RequestDate = %s WHERE host_master_id = %s"
            update_host_status_params = (data.get("Host_uptime"), datetime.now(), request_time, host_id)
            execute_query(update_host_status_query, update_host_status_params, fetch=False)
            logger.info(f"Updated host_status for Hostname {hostname}")
        else:
            # Insert a new entry in host_status table
            insert_host_status_query = "INSERT INTO host_status (host_master_id, uptime, last_updated_date, RequestDate) VALUES (%s, %s, %s, %s)"
            insert_host_status_params = (host_id, data.get("Host_uptime"), datetime.now(), request_time)
            execute_query(insert_host_status_query, insert_host_status_params, fetch=False)
            logger.info(f"Inserted host_status for Hostname {hostname}")


        # Continue processing for service_status and alert_history tables
        for kpi in data["Kpis"]:
            # Check if KpiName is available in services_master table
            service_query = "SELECT * FROM services_master WHERE service_name = %s"
            service_params = (kpi["KpiName"],)
            existing_service = execute_query(service_query, service_params)
            logger.debug(f"Existing service for KpiName {kpi['KpiName']}: {existing_service}")

            if not existing_service:
                # Insert into services_master if not present
                insert_service_query = "INSERT INTO services_master (service_name, service_sub_type) VALUES (%s, %s)"
                insert_service_params = (kpi["KpiName"], kpi["KpiSubType"])
                execute_query(insert_service_query, insert_service_params)
                logger.info(f"Inserted service for KpiName {kpi['KpiName']}")

            # Get the service_id for the current KpiName
            service_id_query = "SELECT id FROM services_master WHERE service_name = %s"
            service_id_params = (kpi["KpiName"],)
            service_id_result = execute_query(service_id_query, service_id_params)
            service_id = service_id_result[0]["id"] if service_id_result else None
            logger.debug(f"Service ID for KpiName {kpi['KpiName']}: {service_id}")

            for key in kpi["Keys"]:
                # Check if KeyName is available in services_details table
                key_query = "SELECT * FROM services_details WHERE service_id = %s AND service_key_name = %s"
                key_params = (service_id, key["KeyName"])
                existing_key = execute_query(key_query, key_params)
                logger.debug(f"Existing key for KeyName {key['KeyName']}: {existing_key}")

                if not existing_key:
                    # Insert into services_details if not present
                    threshold_value = 80.0 if kpi["KpiSubType"] == "P" else 0 if kpi["KpiSubType"] == "B" else 1000
                    insert_key_query = "INSERT INTO services_details (service_id, service_key_name, threshold_value, severity) VALUES (%s, %s, %s, %s)"
                    insert_key_params = (service_id, key["KeyName"], threshold_value, "s3")
                    execute_query(insert_key_query, insert_key_params)
                    logger.info(f"Inserted key for KeyName {key['KeyName']}")

                # Check if service is available in service_status table
                status_query = "SELECT * FROM service_status WHERE service_id = %s AND service_key_name = %s"
                status_params = (service_id, key["KeyName"])
                existing_status = execute_query(status_query, status_params)
                logger.debug(f"Existing status for KeyName {key['KeyName']}: {existing_status}")

                # Initialize last_service_key_value here
                last_service_key_value = None

                if not existing_status:
                    # Check if KeyName is available in services_details table
                    key_query = "SELECT * FROM services_details WHERE service_id = %s AND service_key_name = %s"
                    key_params = (service_id, key["KeyName"])
                    existing_key = execute_query(key_query, key_params)

                    # Get the last_service_key_value for the current KeyName
                    last_service_key_value_query = "SELECT service_key_value FROM service_status WHERE host_id = %s AND service_id = %s AND service_key_name = %s ORDER BY last_updated_date DESC LIMIT 1"
                    last_service_key_value_params = (host_id, service_id, key["KeyName"])
                    last_service_key_value_result = execute_query(last_service_key_value_query, last_service_key_value_params)

                    if last_service_key_value_result:
                        last_service_key_value = last_service_key_value_result[0]["service_key_value"]

                    insert_status_query = "INSERT INTO service_status (host_id, service_id, service_details_id, service_key_name, service_key_value, service_key_desc, last_updated_date, alert_gen_flag, last_service_key_value, RequestDate) VALUES (%s, %s, %s, %s, %s, %s, %s, 1, %s, %s)"
                    if existing_key:
                        insert_status_params = (host_id, service_id, existing_key[0]["id"], key["KeyName"], key["KeyValue"], key["KeyDesc"], datetime.now(), last_service_key_value, request_time)
                    else:
                        insert_status_params = (host_id, service_id, None, key["KeyName"], key["KeyValue"], key["KeyDesc"], datetime.now(), last_service_key_value, request_time)

                    execute_query(insert_status_query, insert_status_params)
                    logger.info(f"Inserted status for KeyName {key['KeyName']}")
                else:
                    # Update last_service_key_value within the else block
                    last_service_key_value = existing_status[0]["last_service_key_value"]

                    # Get the last_service_key_value for the current KeyName
                    last_service_key_value_query = "SELECT service_key_value FROM service_status WHERE host_id = %s AND service_id = %s AND service_key_name = %s ORDER BY last_updated_date DESC LIMIT 1"
                    last_service_key_value_params = (host_id, service_id, key["KeyName"])
                    last_service_key_value_result = execute_query(last_service_key_value_query, last_service_key_value_params)

                    if last_service_key_value_result:
                        last_service_key_value = last_service_key_value_result[0]["service_key_value"]

                    update_status_query = "UPDATE service_status SET service_key_value = %s, service_key_desc = %s, last_updated_date = %s, alert_gen_flag = 1, last_service_key_value = %s, RequestDate = %s WHERE host_id = %s AND service_id = %s AND service_key_name = %s"
                    update_status_params = (key["KeyValue"], key["KeyDesc"], datetime.now(), last_service_key_value if last_service_key_value is not None else key["KeyValue"], request_time, host_id, service_id, key["KeyName"])
                    execute_query(update_status_query, update_status_params, fetch=False)  # Set fetch=False for UPDATE queries
                    logger.info(f"Updated status for KeyName {key['KeyName']}")

                # Insert into alert_history table
                insert_alert_query = "INSERT INTO alert_history (RequestId, RequestDate, host_id, service_id, service_details_id, service_key_name, service_key_value, service_key_desc, updated_date, Month_Partition, Is_Status_Changed) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

                if existing_key:
                    insert_alert_params = (request_id, request_time, host_id, service_id, existing_key[0]["id"], key["KeyName"], key["KeyValue"], key["KeyDesc"], datetime.now(), request_time.strftime("%Y-%m"), 0)
                else:
                    insert_alert_params = (request_id, request_time, host_id, service_id, None, key["KeyName"], key["KeyValue"], key["KeyDesc"], datetime.now(), request_time.strftime("%Y-%m"), 0)

                # Check if the service_key_value and last_service_key_value are different
                status_difference_query = "SELECT service_key_value, last_service_key_value FROM service_status WHERE host_id = %s AND service_id = %s AND service_details_id = %s AND service_key_name = %s ORDER BY last_updated_date DESC LIMIT 1"
                status_difference_params = (host_id, service_id, insert_alert_params[4], key["KeyName"])
                status_difference_result = execute_query(status_difference_query, status_difference_params)

                if status_difference_result and status_difference_result[0]["service_key_value"] != status_difference_result[0]["last_service_key_value"]:
                    insert_alert_params = (*insert_alert_params[:-1], 1)  # Set Is_Status_Changed to 1
                else:
                    insert_alert_params = (*insert_alert_params[:-1], 0)  # Set Is_Status_Changed to 0


                execute_query(insert_alert_query, insert_alert_params, fetch=False)  # Set fetch=False for INSERT queries
                logger.info(f"Inserted into alert_history for KeyName {key['KeyName']}")



        return jsonify({"message": "KPI stats submitted successfully"}), 200

    except Exception as e:
        logger.error(f"Error in kpi_stats_submit: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5070)
