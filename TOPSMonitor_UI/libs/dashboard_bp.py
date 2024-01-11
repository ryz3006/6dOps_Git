# dashboard_bp.py
from flask import Blueprint, render_template, session, redirect, url_for, jsonify
from libs.db_operations import execute_query, execute_query_u

dashboard_bp = Blueprint('dashboard_bp', __name__, template_folder='templates')

@dashboard_bp.route('/get_dashboard_data', methods=['GET'])
def get_dashboard_data():
    # Query to get the counts
    query1 = "SELECT COUNT(host_master_id) FROM host_status"
    query2 = "SELECT COUNT(*) FROM services_details"
    query3 = "SELECT COUNT(*) FROM service_status where alert_gen_flag='1'"
    query4 = "SELECT COUNT(id) FROM service_status WHERE TIMESTAMPDIFF(MINUTE, last_updated_date, NOW()) < 5"

    try:
        # Execute queries
            result1 = execute_query(query1)
            x_count = result1[0][0] if result1 else 0  # Fetch the count or set to 0 if result is None

            result2 = execute_query(query2)
            y_count_1 = result2[0][0] if result2 else 0

            result3 = execute_query(query3)
            z_count = result3[0][0] if result3 else 0

            result4 = execute_query(query4)
            y_count_2 = result4[0][0] if result3 else 0

            print(f'Output of get dashboard data : {x_count} , {y_count_1}, {y_count_2}, {z_count}')


            data = {
                'x_count': x_count,
                'y_count_1': y_count_1,
                'y_count_2': y_count_2,
                'z_count': z_count
            }
            return jsonify(data)
    except Exception as e:
            print(f"Error executing queries: {e}")

@dashboard_bp.route('/get_table_data', methods=['GET'])
def get_table_data():
    # Execute your SQL query here and fetch data
    query = """
            SELECT hm.hostname, hm.ip, sm.service_name, ss.service_key_name,
                   ss.service_key_value, ss.service_key_desc, ss.last_updated_date
            FROM host_master hm, services_master sm, service_status ss
            WHERE ss.host_id = hm.id AND sm.id = ss.service_id
        """
    print(f"Executing the query - {query}")
    
    # Replace the example data with your actual data
    try:
            # Execute the query
            #result = execute_query_u(query)
            cursor, connection, result = execute_query_u(query)
            print(f"Result is - {result}")

            # Fetch column names
            # columns = [column[0] for column in result.description]
            #print(f"Column names are - {columns}")

            # Fetch data rows
            #data = [dict(zip(row)) for row in result.fetchall()]
            #print(f"Dist data - {data}")

            # Fetch data rows
            ##data = [dict(zip(result.column_names, row)) for row in result.fetchall()]
            ##print(f"Dist data - {data}")


            ##return jsonify(data)
            try:
                 if cursor:
                      data = result
                      print(f"Dist data - {data}")
                      return jsonify(data)
                 else:
                      return jsonify([])
                 
            finally:
                 if cursor:
                      cursor.close()
                 if connection:
                      connection.close()
                           

    except Exception as e:
            print(f"Error executing query: {e}")
            return jsonify([])

@dashboard_bp.route('/alert_history', methods=['GET'])
def alert_history():
    # Execute your SQL query here and fetch data
    query = """
            select ah.RequestDate, hm.hostname, hm.ip, sm.service_name, sd.service_key_name, ah.service_key_desc, ah.service_key_value, ah.alertType from alert_history ah, services_master sm, services_details sd, host_master hm where ah.service_id=sm.id and ah.service_details_id=sd.id and ah.host_id=hm.id and ah.Is_Status_Changed = 1 and TIMESTAMPDIFF(MINUTE, ah.RequestDate, NOW()) < 100440 order by ah.RequestDate DESC;
        """
    print(f"Executing the query for alert histrory - {query}")
    
    # Replace the example data with your actual data
    try:
            # Execute the query
            #result = execute_query_u(query)
            cursor, connection, result = execute_query_u(query)
            print(f"Result for alert history is - {result}")

            # Fetch column names
            # columns = [column[0] for column in result.description]
            #print(f"Column names are - {columns}")

            # Fetch data rows
            #data = [dict(zip(row)) for row in result.fetchall()]
            #print(f"Dist data - {data}")

            # Fetch data rows
            ##data = [dict(zip(result.column_names, row)) for row in result.fetchall()]
            ##print(f"Dist data - {data}")


            ##return jsonify(data)
            try:
                 if cursor:
                      data = result
                      print(f"Dist data - {data}")
                      return jsonify(data)
                 else:
                      return jsonify([])
                 
            finally:
                 if cursor:
                      cursor.close()
                 if connection:
                      connection.close()
                           

    except Exception as e:
            print(f"Error executing query: {e}")
            return jsonify([])

@dashboard_bp.route('/dashboard')
def dashboard():
    if 'username' in session:
        # Query to get the counts
        query1 = "SELECT COUNT(host_master_id) FROM host_status"
        query2 = "SELECT COUNT(*) FROM services_details"
        query3 = "SELECT COUNT(*) FROM service_status where alert_gen_flag='1'"

        try:
            # Execute queries
            result1 = execute_query(query1)
            x_count = result1[0][0] if result1 else 0  # Fetch the count or set to 0 if result is None

            result2 = execute_query(query2)
            y_count = result2[0][0] if result2 else 0

            result3 = execute_query(query3)
            z_count = result3[0][0] if result3 else 0

            # Debugging statements
            print(f"x_count: {x_count}")
            print(f"y_count: {y_count}")
            print(f"z_count: {z_count}")

            # Debugging statements
            print(f"x_count: {x_count}")
            print(f"y_count: {y_count}")
            print(f"z_count: {z_count}")



            # Render the HTML template with the counts
            return render_template('index.html', x_count=x_count, y_count=y_count, z_count=z_count)

        except Exception as e:
            print(f"Error executing queries: {e}")

        # If an error occurs, return a generic response
        return render_template('index.html', x_count=0, y_count=0, z_count=0)
    else:
        return redirect(url_for('login_bp.login'))