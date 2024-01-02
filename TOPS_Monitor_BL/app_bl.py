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

db = mysql.connector.connect(**db_config)

logger.info("Database connection successful!")


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

        if "KpiType" in data and data["KpiType"] == "Service" and "Kpis" in data:
            for kpi in data["Kpis"]:
                if "KpiName" in kpi:
                    logger.info(f"Processing KpiName: {kpi['KpiName']}")
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
                        if "KeyName" in key:
                            logger.info(f"Processing KeyName: {key['KeyName']}")
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

                            
                            # Insert or update values in service_status table
                            if not existing_status:
                                # Check if KeyName is available in services_details table
                                key_query = "SELECT * FROM services_details WHERE service_id = %s AND service_key_name = %s"
                                key_params = (service_id, key["KeyName"])
                                existing_key = execute_query(key_query, key_params)

                                insert_status_query = "INSERT INTO service_status (service_id, service_details_id, service_key_name, service_key_value, service_key_desc, last_updated_date) VALUES (%s, %s, %s, %s, %s, %s)"

                                if existing_key:
                                    insert_status_params = (service_id, existing_key[0]["id"], key["KeyName"], key["KeyValue"], key["KeyDesc"], datetime.now())
                                else:
                                    insert_status_params = (service_id, None, key["KeyName"], key["KeyValue"], key["KeyDesc"], datetime.now())

                                execute_query(insert_status_query, insert_status_params)
                                logger.info(f"Inserted status for KeyName {key['KeyName']}")
                            else:
                                update_status_query = "UPDATE service_status SET service_key_value = %s, service_key_desc = %s, last_updated_date = %s WHERE service_id = %s AND service_key_name = %s"
                                update_status_params = (key["KeyValue"], key["KeyDesc"], datetime.now(), service_id, key["KeyName"])
                                execute_query(update_status_query, update_status_params, fetch=False)  # Set fetch=False for UPDATE queries
                                logger.info(f"Updated status for KeyName {key['KeyName']}")


                            # Insert into alert_history table
                            insert_alert_query = "INSERT INTO alert_history (service_id, service_details_id, service_key_name, service_key_value, service_key_desc, updated_date, Month_Partition) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                            insert_alert_params = (service_id, existing_key[0]["id"] if existing_key else None, key["KeyName"], key["KeyValue"], key["KeyDesc"], datetime.now(), datetime.now().strftime("%Y-%m"))
                            execute_query(insert_alert_query, insert_alert_params, fetch=False)  # Set fetch=False for INSERT queries
                            logger.info(f"Inserted into alert_history for KeyName {key['KeyName']}")


        return jsonify({"message": "KPI stats submitted successfully"}), 200

    except Exception as e:
        logger.error(f"Error in kpi_stats_submit: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5002)