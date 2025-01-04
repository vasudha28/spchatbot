from flask import Flask, session, request, jsonify, render_template, redirect, url_for, flash
from flask_pymongo import PyMongo
from pymongo import MongoClient
from flask_cors import CORS
from bson import ObjectId
from datetime import datetime
import re

app = Flask(__name__)
CORS(app)

app.secret_key = '1891235489'

app.config["MONGO_URI"] = "mongodb+srv://vasudha:vasudha@cluster0.0vkno.mongodb.net/bfsi?authSource=admin&retryWrites=true&w=majority&readPreference=primary"
mongo = PyMongo(app)

try:
    client = MongoClient('mongodb+srv://vasudha:vasudha@cluster0.0vkno.mongodb.net/bfsi?authSource=admin&retryWrites=true&w=majority&readPreference=primary')
    db = client.get_database("bfsi")
    print("Databases:", client.list_database_names())
    print("Connection successful!")
except Exception as e:
    print("Connection failed:", e)


@app.route('/')
def login_redirect():
    return render_template('login.html')


@app.route('/register/user', methods=['GET', 'POST'])
def register_user_page():
    if request.method == 'POST':
        # Get form data
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirmPassword')

        # Validation
        if not username or not email or not password or not confirm_password:
            flash('All fields are required.', 'error')
            return redirect(url_for('register_user_page'))
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('register_user_page'))

        # Check if user already exists
        existing_user = mongo.db.users.find_one({'username': username})
        if existing_user:
            flash('Username already exists.', 'error')
            return redirect(url_for('register_user_page'))

        # Store user in the database
        try:
            mongo.db.users.insert_one({
                'username': username,
                'email': email,
                'password': password,
                'role': 'user'  # Default role for registration
            })
            flash('Successfully registered! Please login.', 'success')
            return redirect(url_for('login_page'))
        except Exception as e:
            flash('An error occurred while registering. Please try again.', 'error')
            return redirect(url_for('register_user_page'))

    # Render the registration page for GET requests
    return render_template('register_user.html')



@app.route('/register/admin', methods=['GET', 'POST'])
def register_admin():
    if request.method == 'POST':
        try:
            data = request.get_json()
            username = data.get('username')
            work_email = data.get('work_email')
            password = data.get('password')
            role = data.get('role', 'admin')  # Default role: admin

            # Validate input fields
            if not username or not work_email or not password:
                return jsonify({'error': 'All fields are required!'}), 400

            if not re.match(r"[^@]+@[^@]+\.[^@]+", work_email):
                return jsonify({'error': 'Invalid email format!', 'field': 'work_email'}), 400

            # Check for duplicates in MongoDB
            if mongo.db.admin.find_one({'username': username}):
                return jsonify({'error': 'Username already exists!', 'field': 'username'}), 400

            if mongo.db.admin.find_one({'work_email': work_email}):
                return jsonify({'error': 'Email already registered!', 'field': 'work_email'}), 400

            # Store the admin data in MongoDB
            mongo.db.admin.insert_one({
                'username': username,
                'work_email': work_email,
                'password': password,  # Store hashed password in production
                'role': role
            })

            return jsonify({'message': 'Admin registered successfully!', 'redirect': '/login'}), 201

        except Exception as e:
            print(f"Error during registration: {e}")
            return jsonify({'error': 'An error occurred during registration. Please try again.'}), 500

    # Render the admin registration form for GET requests
    return render_template('register_admin.html')



@app.route('/register/superadmin', methods=['GET', 'POST'])
def register_superadmin():
    if request.method == 'POST':
        try:
            data = request.get_json()
            username = data.get('username')
            work_email = data.get('work_email')
            password = data.get('password')

            # Validate input fields
            if not username or not work_email or not password:
                return jsonify({'error': 'All fields are required!'}), 400

            if not re.match(r"[^@]+@[^@]+\.[^@]+", work_email):
                return jsonify({'error': 'Invalid email format!', 'field': 'work_email'}), 400


            # Save Super Admin details to the database
            mongo.db.superadmin.insert_one({
                'username': username,
                'work_email': work_email,
                'password': password  # Store hashed password in production
            })

            return jsonify({'message': 'Super Admin registered successfully!', 'redirect': '/login'}), 201

        except Exception as e:
            print(f"Error during Super Admin registration: {e}")
            return jsonify({'error': 'An error occurred during registration. Please try again.'}), 500

    # Render the Super Admin registration page for GET requests
    return render_template('register_superadmin.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    if request.method == 'POST':
        try:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
            role = data.get('role')

            # Validate input
            if not username or not password or not role:
                return jsonify({'error': 'All fields are required!'}), 400

            # Query respective collection based on role
            if role == 'user':
                user = mongo.db.users.find_one({'username': username, 'password': password})
                if user:
                    return jsonify({'redirect': '/user.html'}), 200
            elif role == 'admin':
                admin = mongo.db.admin.find_one({'username': username, 'password': password})
                if admin:
                    return jsonify({'redirect': '/admin.html'}), 200
            elif role == 'superadmin':
                superadmin = mongo.db.superadmin.find_one({'username': username, 'password': password})
                if superadmin:
                    return jsonify({'redirect': '/sa.html'}), 200

            # If no match is found
            return jsonify({'error': 'Invalid username, password, or role.'}), 401

        except Exception as e:
            print(f"Error during login: {e}")
            return jsonify({'error': 'An error occurred during login. Please try again.'}), 500

@app.route('/user')
def user():
    try:
        # Explicitly fetch only scenarios marked as visible to users
        scenarios = list(mongo.db.admin.find({
            "visible_to_users": True
        }).sort('user_approval_date', -1))
        return render_template('index.html', scenarios=scenarios)
    except Exception as e:
        print(f"Error fetching scenarios: {e}")
        return jsonify({"error": "Failed to fetch scenarios"}), 500
    

# Routes for rendering additional HTML templates
@app.route('/user.html')
def user_page():
    return render_template('user.html')

@app.route('/admin.html')
def admin_page():
    return render_template('admin.html')

@app.route('/sa.html')
def sa_page():
    return render_template('sa.html')


@app.route('/admindashboard')
def admin_dashboard():
    scenarios = mongo.db.admin.find()
    return render_template('admindashboard.html', scenarios=scenarios)

@app.route('/summary')
def summary():
    return render_template('summary.html')

@app.route('/get_prompt', methods=['POST'])
def get_prompt():
    try:
        request_data = request.json
        print("Received Request Data:", request_data)

        scenario_id = request.json.get('scenario_id', '')
        print(f"Extracted Scenario ID: {scenario_id}")

        if not scenario_id:
            return jsonify({"error": "No scenario ID provided"}), 400
        
        try:
            object_id = ObjectId(scenario_id)
        except Exception as e:
            print(f"Invalid ObjectId: {e}")
            return jsonify({"error": "Invalid scenario ID format"}), 400
        
        scenario_data = mongo.db.admin.find_one({"_id": object_id})

        if scenario_data and "prompt" in scenario_data:
            updated_prompt = scenario_data["prompt"]
            return jsonify({"prompt": updated_prompt})
        else:
            return jsonify({"error": "Scenario not found"}), 404
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Failed to fetch prompt"}), 500

@app.route('/index')
def question():
    scenarios = mongo.db.admin.find({"visible_to_users": True})
    return render_template('index.html', scenarios=scenarios)


@app.route('/create', methods=['POST'])
def create_scenario():
    try:
        data = request.json
        result = mongo.db.admin.insert_one({
            "scenario": data['scenario'],
            "prompt": data['prompt'],
            "question": data['question'],
            "visible_to_users": False
        })
        return jsonify({"message": "Roleplay created successfully", "id": str(result.inserted_id)}), 201
    except Exception as e:
        print(f"Error creating scenario: {e}")
        return jsonify({"error": "Failed to create scenario"}), 500


@app.route('/history', methods=['GET'])
def get_history():
    try:
        history = mongo.db.admin.find()
        return jsonify([
            {
                "_id": str(doc['_id']),
                "scenario": doc.get('scenario', ''),
                "prompt": doc.get('prompt', ''),
                "question": doc.get('question', ''),
                "visible_to_users": doc.get('visible_to_users', False),
                "visible_to_admin": doc.get('visible_to_admin', False)
            }
            for doc in history
        ]), 200
    except Exception as e:
        print(f"Error fetching history: {e}")
        return jsonify({"error": "Failed to fetch history"}), 500
    


@app.route('/delete/<scenario_id>', methods=['DELETE'])
def delete_scenario(scenario_id):
    try:
        object_id = ObjectId(scenario_id)
        result = mongo.db.admin.delete_one({'_id': object_id})
        
        if result.deleted_count > 0:
            return jsonify({"message": "Scenario deleted successfully"}), 200
        else:
            return jsonify({"error": "Scenario not found"}), 404
    except Exception as e:
        print(f"Error deleting scenario: {e}")
        return jsonify({"error": "Failed to delete scenario"}), 500
    

@app.route('/delete-batch', methods=['POST'])
def delete_batch():
    try:
        scenario_ids = request.json.get('ids', [])
        if not scenario_ids:
            return jsonify({"error": "No scenarios specified"}), 400

        object_ids = [ObjectId(id) for id in scenario_ids]
        result = mongo.db.admin.delete_many({'_id': {'$in': object_ids}})
        
        if result.deleted_count > 0:
            return jsonify({
                "message": f"Successfully deleted {result.deleted_count} scenarios",
                "deleted_count": result.deleted_count
            }), 200
        else:
            return jsonify({"error": "No scenarios found to delete"}), 404
    except Exception as e:
        print(f"Error in batch delete: {e}")
        return jsonify({"error": "Failed to delete scenarios"}), 500
    


@app.route('/toggle_admin_visibility', methods=['POST'])
def toggle_admin_visibility():
    """Super admin endpoint to toggle visibility for admins"""
    try:
        scenario_ids = request.json.get('ids', [])
        if not scenario_ids:
            return jsonify({"error": "No scenarios specified"}), 400

        object_ids = [ObjectId(id) for id in scenario_ids]
        
        # Update visibility for admins
        result = mongo.db.admin.update_many(
            {'_id': {'$in': object_ids}},
            {'$set': {'visible_to_admin': True}}
        )
        
        # # Set others to not visible to admin
        # mongo.db.admin.update_many(
        #     {'_id': {'$nin': object_ids}},
        #     {'$set': {'visible_to_admin': False}}
        # )

        return jsonify({
            "message": f"Successfully updated admin visibility for {result.modified_count} scenarios",
            "modified_count": result.modified_count
        }), 200
    except Exception as e:
        print(f"Error toggling admin visibility: {e}")
        return jsonify({"error": "Failed to update scenarios"}), 500

@app.route('/toggle_visibility', methods=['POST'])
def toggle_visibility():
    """Super admin endpoint to toggle visibility for users"""
    try:
        scenario_ids = request.json.get('ids', [])
        if not scenario_ids:
            return jsonify({"error": "No scenarios specified"}), 400

        object_ids = [ObjectId(id) for id in scenario_ids]
        
        # Update visibility for users
        result = mongo.db.admin.update_many(
            {'_id': {'$in': object_ids}},
            {'$set': {'visible_to_users': True}}
        )

        return jsonify({
            "message": f"Successfully updated visibility for {result.modified_count} scenarios",
            "modified_count": result.modified_count
        }), 200
    except Exception as e:
        print(f"Error toggling visibility: {e}")
        return jsonify({"error": "Failed to update scenarios"}), 500
    
@app.route('/admin')
def admin_view():
    """Route for the regular admin dashboard"""
    return render_template('admin_dashboard.html')

@app.route('/admin/scenarios')
def get_admin_scenarios():
    """Get scenarios that are visible to admin (approved by super admin)"""
    try:
        # Get all scenarios that super admin has made visible to admin
        scenarios = list(mongo.db.admin.find({"visible_to_admin": True}))
        return jsonify([
            {
                "_id": str(doc['_id']),
                "scenario": doc.get('scenario', ''),
                "prompt": doc.get('prompt', ''),
                "question": doc.get('question', ''),
                "visible_to_users": doc.get('visible_to_users', False)
            }
            for doc in scenarios
        ]), 200
    except Exception as e:
        print(f"Error fetching admin scenarios: {e}")
        return jsonify({"error": "Failed to fetch scenarios"}), 500

@app.route('/admin/toggle_visibility', methods=['POST'])
def admin_toggle_visibility():
    """Admin endpoint to toggle user visibility"""
    try:
        scenario_ids = request.json.get('ids', [])
        action = request.json.get('action', 'add')  # Add this line
        if not scenario_ids:
            return jsonify({"error": "No scenarios specified"}), 400

        object_ids = [ObjectId(id) for id in scenario_ids]
        
        # Verify these scenarios are visible to admin first
        visible_to_admin = mongo.db.admin.count_documents({
            '_id': {'$in': object_ids},
            'visible_to_admin': True
        })
        
        if visible_to_admin != len(scenario_ids):
            return jsonify({"error": "Unauthorized access to some scenarios"}), 403

        # Update visibility for users
        if action == 'add':
            result = mongo.db.admin.update_many(
                {'_id': {'$in': object_ids}},
                {
                    '$set': {
                        'visible_to_users': True,
                        'user_approval_date': datetime.now()
                    }
                }
            )
        else:
            result = mongo.db.admin.update_many(
                {'_id': {'$in': object_ids}},
                {
                    '$set': {
                        'visible_to_users': False
                    },
                    '$unset': {
                        'user_approval_date': ''
                    }
                }
            )

        return jsonify({
            "message": f"Successfully {'added to' if action == 'add' else 'removed from'} user view",
            "modified_count": result.modified_count
        }), 200
    except Exception as e:
        print(f"Error toggling user visibility: {e}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/remove_admin_visibility', methods=['POST'])
def remove_admin_visibility():
    """Remove scenarios from admin view"""
    try:
        scenario_ids = request.json.get('ids', [])
        if not scenario_ids:
            return jsonify({"error": "No scenarios specified"}), 400

        object_ids = [ObjectId(id) for id in scenario_ids]
        
        result = mongo.db.admin.update_many(
            {'_id': {'$in': object_ids}},
            {'$set': {'visible_to_admin': False}}
        )

        return jsonify({
            "message": f"Successfully removed admin visibility for {result.modified_count} scenarios",
            "modified_count": result.modified_count
        }), 200
    except Exception as e:
        print(f"Error removing admin visibility: {e}")
        return jsonify({"error": "Failed to update scenarios"}), 500

@app.route('/admin/current-user-scenarios')
def get_current_user_scenarios():
    """Get scenarios that are currently visible to users"""
    try:
        scenarios = mongo.db.admin.find({"visible_to_users": True})
        return jsonify([{
            "_id": str(doc['_id']),
            "scenario": doc.get('scenario', ''),
            "prompt": doc.get('prompt', ''),
            "question": doc.get('question', ''),
            "approval_date": doc.get('user_approval_date', None)
        } for doc in scenarios]), 200
    except Exception as e:
        print(f"Error fetching user scenarios: {e}")
        return jsonify({"error": "Failed to fetch scenarios"}), 500

@app.route('/superadmin/toggle_admin_visibility', methods=['POST'])
def superadmin_toggle_admin_visibility():
    try:
        scenario_ids = request.json.get('ids', [])
        action = request.json.get('action', 'add')  # 'add' or 'remove'
        
        if not scenario_ids:
            return jsonify({"error": "No scenarios specified"}), 400

        object_ids = [ObjectId(id) for id in scenario_ids]
        
        if action == 'add':
            # Update visibility and add approval date for admin
            result = mongo.db.admin.update_many(
                {'_id': {'$in': object_ids}},
                {
                    '$set': {
                        'visible_to_admin': True,
                        'admin_approval_date': datetime.now().isoformat()
                    }
                }
            )
        else:  # remove
            # Remove visibility from admin
            result = mongo.db.admin.update_many(
                {'_id': {'$in': object_ids}},
                {
                    '$set': {'visible_to_admin': False},
                    '$unset': {'admin_approval_date': ''}
                }
            )

        return jsonify({
            "message": f"Successfully {'added to' if action == 'add' else 'removed from'} admin view",
            "modified_count": result.modified_count
        }), 200
    except Exception as e:
        print(f"Error toggling admin visibility: {e}")
        return jsonify({"error": "Failed to update scenarios"}), 500

@app.route('/superadmin/toggle_user_visibility', methods=['POST'])
def superadmin_toggle_user_visibility():
    """Super admin endpoint to toggle visibility for users"""
    try:
        scenario_ids = request.json.get('ids', [])
        action = request.json.get('action', 'add')  # 'add' or 'remove'
        
        if not scenario_ids:
            return jsonify({"error": "No scenarios specified"}), 400

        object_ids = [ObjectId(id) for id in scenario_ids]
        
        update_data = {
            '$set': {
                'visible_to_users': action == 'add',
                'user_approval_date': datetime.now().isoformat() if action == 'add' else None
            }
        }

        result = mongo.db.admin.update_many(
            {'_id': {'$in': object_ids}},
            update_data
        )

        return jsonify({
            "message": f"Successfully {'added to' if action == 'add' else 'removed from'} user view",
            "modified_count": result.modified_count
        }), 200
    except Exception as e:
        print(f"Error toggling user visibility: {e}")
        return jsonify({"error": "Failed to update scenarios"}), 500


@app.route('/superadmin/current-user-scenarios', methods=['GET'])
def superadmin_get_user_scenarios():
    """Get scenarios that are currently visible to users (for super admin view)"""
    try:
        scenarios = mongo.db.admin.find({"visible_to_users": True})
        return jsonify([{
            "_id": str(doc['_id']),
            "scenario": doc.get('scenario', ''),
            "approval_date": doc.get('user_approval_date', None),
            "admin_approval_date": doc.get('admin_approval_date', None)
        } for doc in scenarios]), 200
    except Exception as e:
        print(f"Error fetching user scenarios: {e}")
        return jsonify({"error": "Failed to fetch scenarios"}), 500


@app.route('/superadmin/current-admin-scenarios', methods=['GET'])
def superadmin_get_admin_scenarios():
    """Get scenarios that are currently visible to admin"""
    try:
        scenarios = mongo.db.admin.find({"visible_to_admin": True})
        return jsonify([{
            "_id": str(doc['_id']),
            "scenario": doc.get('scenario', ''),
            "approval_date": doc.get('admin_approval_date', None),
            "user_visible": doc.get('visible_to_users', False)
        } for doc in scenarios]), 200
    except Exception as e:
        print(f"Error fetching admin scenarios: {e}")
        return jsonify({"error": "Failed to fetch scenarios"}), 500


if __name__ == '__main__':
    app.run(debug=True)