from typing import Dict, List, Optional
import uuid
import firebase_admin
from firebase_admin import credentials, firestore, auth
# from ...api import safe_get_env_var,utils
import json
from mockfirestore import MockFirestore

from api.utils import generate_random_string
from common.utils import safe_get_env_var
from google.cloud.firestore_v1.base_query import FieldFilter

from ratelimit import limits

# firebase_cert_config_str = safe_get_env_var("FIREBASE_CERT_CONFIG")
cert_env = json.loads(safe_get_env_var("FIREBASE_CERT_CONFIG"))
cred = credentials.Certificate(cert_env)
firebase_admin.initialize_app(credential=cred)

mockfirestore = MockFirestore() #Only used when testing 
ONE_MINUTE = 1*60

# add logger
import logging
logger = logging.getLogger(__name__)
# set logger to standard out
logger.addHandler(logging.StreamHandler())
# set log level
logger.setLevel(logging.INFO)

user_collection = "users"
verification_collection = "verification"
resources_collection = "resources"
mood_collection = "moods"
wallet_collection = "wallet"
calendar_collection ="calendar"

@limits(calls=100, period=ONE_MINUTE)
def verify_id_token(id_token):
    try:
        decoded_token = firebase_admin.auth.verify_id_token(id_token)
        print("Decoded Token:", decoded_token)
        return True
    except:
        raise ValueError("token issue")

@limits(calls=100, period=ONE_MINUTE)
def update_user_step_one(email, user_id):
    try:
        auth.update_user(
            uid=user_id,
        email=email,
        email_verified=False,
        disabled=False)
    except:
        return False
    return True

@limits(calls=100, period=ONE_MINUTE)
def update_therapist_information(user_id, therapist_information):
    db=get_db()
    user_ref = db.collection(user_collection).document(user_id)

    try:
        user_ref.set(therapist_information, merge=True)
    except:
        logger.error("Error updating user")
        return False
    return True

@limits(calls=100, period=ONE_MINUTE)
def update_client_information(user_id, client_information):
    db=get_db()
    user_ref = db.collection(user_collection).document(user_id)

    try:
        user_ref.set(client_information, merge=True)
    except:
        logger.error("Error updating user")
        return False
    return True

@limits(calls=100, period=ONE_MINUTE)
def update_therapy_patient_requests(userId, newPatientId):
    db=get_db()
    therapist_collection_ref = db.collection(user_collection).document(userId)
    try:
        therapist_collection_ref.set({
            'pending_requests': array_union(newPatientId) 
            }, merge=True)
        return
    except Exception as e:
        raise Exception(e)
    
@limits(calls=100, period=ONE_MINUTE)
def update_therapy_patient_cancellation(therapist_id, patient_id):
    try:
        db = get_db()
        therapist_doc_ref = db.collection(user_collection).document(therapist_id)
        therapist_data = get_user_data(therapist_id)

        if not therapist_data:
            raise ValueError(f"User data not found for user_id {therapist_id}")

        pending_requests = therapist_data.get('pending_requests', [])
        if patient_id in pending_requests:
            pending_requests = [req for req in pending_requests if req != patient_id]
        else:
            logging.warning(f"User ID {therapist_id} not in pending requests.")
        therapist_doc_ref.set(
            {
                # 'accepted_requests': array_union(patient_id),
                'pending_requests': pending_requests,
            },
            merge=True
        )
        logging.info(f"Successfully updated requests for user_id {therapist_id}.")
    except Exception as e:
        logging.error(f"An error occurred while updating approvals: {e}")
        raise

@limits(calls=100, period=ONE_MINUTE)
def fetch_patient_lists(user_id, patient_list: str):
    pending_request_list = []
    try:
        user_data = get_user_data(user_id)

        if not user_data:
            raise ValueError(f"User data not found for user_id {user_id}")

        pending_requests = user_data.get(patient_list, [])


        for patient_id in pending_requests:
            patient_data = get_user_data(patient_id)
            if patient_data:
                pending_request_list.append(patient_data)

        return pending_request_list
    except Exception as e:
        raise Exception(e)

@limits(calls=100, period=ONE_MINUTE)
def update_therapy_patient_approvals(user_id, patient_id):
    try:
        db = get_db()
        therapist_doc_ref = db.collection(user_collection).document(user_id)
        therapist_data = get_user_data(user_id)

        if not therapist_data:
            raise ValueError(f"User data not found for user_id {user_id}")

        pending_requests = therapist_data.get('pending_requests', [])
        if patient_id in pending_requests:
            pending_requests = [req for req in pending_requests if req != patient_id]
        else:
            logging.warning(f"User ID {user_id} not in pending requests.")
        therapist_doc_ref.set(
            {
                'accepted_requests': array_union(patient_id),
                'pending_requests': pending_requests,
            },
            merge=True
        )
        logging.info(f"Successfully updated requests for user_id {user_id}.")
    except Exception as e:
        logging.error(f"An error occurred while updating approvals: {e}")
        raise




@limits(calls=100, period=ONE_MINUTE)
def update_therapy_patient_denials(user_id, patient_id, rejection_message):
    try:
        db = get_db()
        therapist_doc_ref = db.collection(user_collection).document(user_id)
        user_data = get_user_data(user_id)

        if not user_data:
            raise ValueError(f"User data not found for user_id {user_id}")

        pending_requests = user_data.get('pending_requests', [])
        if patient_id in pending_requests:
            pending_requests = [req for req in pending_requests if req != patient_id]
        else:
            logging.warning(f"User ID {user_id} not in pending requests.")
        therapist_doc_ref.set(
            {
                'denied_requests': array_union(patient_id),
                'pending_requests': pending_requests,
            },
            merge=True
        )
        # remove therapist from therapistId of client
        patient_doc_ref = db.collection(user_collection).document(patient_id)
        date_string = f'{datetime.now():%Y-%m-%d}'
        patient_doc_ref.set(
            {
                'therapist_id': "",
                'therapy_denials': array_union({
                    "therapist_id": user_id,
                    "rejection_message": rejection_message,
                    "date": date_string
                }),
            },
            merge=True
        )

        logging.info(f"Successfully updated requests for user_id {user_id}.")
    except Exception as e:
        logging.error(f"An error occurred while updating approvals: {e}")
        raise


@limits(calls=100, period=ONE_MINUTE)
def create_user_verification_key(user_id):
    
    # update user collection by adding a randomly generated key
    # send this randomly generated key to the user's  email
    # when the link has been clicked, call the api to verify the user 
    db=get_db()
    random_user_code = generate_random_string(32)

    user_ref = db.collection(verification_collection).document(user_id)
    try:
        user_ref.set({"random_user_code": random_user_code, "email_verified":False}, merge=True)
    except:
        logger.error("Error creating User")
        return False
    return random_user_code

@limits(calls=100, period=ONE_MINUTE)
def get_user_email_from_user_id(user_id):
    
    user = auth.get_user(user_id)
    return user.email

# @limits(calls=100, period=ONE_MINUTE)
def find_user_by_random_user_code(random_user_code: str):
    """
    Finds a user by their random user code.

    Args:
        random_user_code (str): The random user code to search for.

    Returns:
        Optional[str]: The ID of the user document if found, else None.
    """
    try:
        db = get_db()
        docs = db.collection(verification_collection).where(filter=FieldFilter("random_user_code", "==", random_user_code)).stream()
        if not docs:
            return None
        for doc in docs:
            return doc.id
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    
@limits(calls=100, period=ONE_MINUTE)
def verify_user_from_code(random_user_code):
    # find the user based on the user key as defined in create_user_verification_key()
    # if the user has been found, update the user
    does_user_exist = find_user_by_random_user_code(random_user_code=random_user_code)
    if not does_user_exist:
        raise ValueError('User does not exist')
    uid = does_user_exist
    try:
        db=get_db()
        user_ref = db.collection(verification_collection).document(uid)
        # Retrieve the user's email from the Firebase auth object
        user_record = auth.get_user(uid)
        user_email = user_record.email

        # Update Firestore with email_verified and email
        user_ref.set({"email_verified": True, "email": user_email}, merge=True)
        auth.update_user(
        uid,
        email_verified=True,)
    except Exception as e:
        logger.debug("Error" + (str(e)))
        raise Exception(e)
    return True

def get_db():
    if safe_get_env_var("ENVIRONMENT") == "test":
        return mockfirestore
    
    return firestore.client()

def array_union(*array_value):
    return firestore.ArrayUnion(array_value)

# @limits(calls=100, period=ONE_MINUTE)
def get_user_data(user_id):
    print(user_id)
    try:
        db = get_db()  # this connects to our Firestore database
        doc = db.collection(user_collection).document(user_id).get()
        if doc.exists:
            dict = doc.to_dict()
            return dict
        else:
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# @limits(calls=100, period=ONE_MINUTE)
def get_user_verification_data(user_id):
    try:
        db = get_db()  # this connects to our Firestore database
        doc = db.collection(verification_collection).document(user_id).get()
        if doc.exists:
            dict = doc.to_dict()
            return dict
        else:
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

@limits(calls=100, period=ONE_MINUTE)
def fetch_general_topics():
    try:
        db = get_db()  # this connects to our Firestore database
        doc = db.collection(resources_collection).document("topics").get()
        if doc.exists:
            dict = doc.to_dict()
            return dict["interest"]
        else:
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    
@limits(calls=100, period=ONE_MINUTE)
def fetch_therapists():
    try:
        db = get_db() 
        query = db.collection(user_collection).where(filter=FieldFilter("user_type", "==", "therapist"))
        # Execute query and get documents
        docs = query.stream()
        if not docs:
            return None
        # Convert documents to list of dictionaries with relevant fields
        else:
            therapists = []
            for doc in docs:
                therapist_data = doc.to_dict()
                therapists.append(therapist_data)
            return therapists
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    
@limits(calls=100, period=ONE_MINUTE)
def check_therapist_selection(user_id):
    try:
        user_data = get_user_verification_data(user_id)
        print(user_data)
        return user_data['therapist_id']
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

@limits(calls=100, period=ONE_MINUTE)
def is_user_verified(user_id):
    try:
        user_data = get_user_verification_data(user_id)
        print(user_data)
        return user_data['email_verified']
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

@limits(calls=100, period=ONE_MINUTE)
def is_user_onboarded(user_id):
    try:
        user_data = get_user_data(user_id)
        print(user_data)
        if 'selected_topics' in user_data:
           return True
        else:
            return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

@limits(calls=100, period=ONE_MINUTE)
def is_user_updated(user_id):
    try:
        user_data = get_user_data(user_id)
        print(user_data)
        if(user_data):
            if ('display_name' in user_data and 'birthday' in user_data and 'location' in user_data and 'pronouns' in user_data):
                return True
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
from datetime import datetime


@limits(calls=100, period=ONE_MINUTE)
def set_patient_mood(user_id, mood_value):
    try:
        db=get_db()
        mood_ref = db.collection(mood_collection).document(user_id)
        date_string = f'{datetime.now():%Y-%m-%d}'
        mood_ref.set({f"{date_string}":mood_value}, merge=True)
    except Exception as e:
        logger.debug("Error" + (str(e)))
        raise Exception(e)
    return True

@limits(calls=100, period=ONE_MINUTE)
def fetch_patients_moods(user_id):
    try:
        db = get_db()  # this connects to our Firestore database
        doc = db.collection(mood_collection).document(user_id).get()
        if doc.exists:
            dict = doc.to_dict()
            return dict
        else:
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

@limits(calls=100, period=ONE_MINUTE)
def get_user_type(user_id):
    # should be either therapist or patient
    return "patient"

@limits(calls=100, period=ONE_MINUTE)
# def save_user_chat(user_id):

def get_user_id_from_token(token):
    # TODO: Implement function
    pass


test_collection = "test"

def test_firebase():
    db = get_db()  # this connects to our Firestore database
    docs = db.collection(test_collection).stream()

    for doc in docs:
        adict = doc.to_dict()
        adict["id"] = doc.id
        return adict


@limits(calls=100, period=ONE_MINUTE)
def update_patient_balance(user_id: str, transaction_id:str, amount:any, transaction_time: any, phone_number: str, first_name: str, last_name: str):
    """
    Fetch and update the patient's wallet balance by adding the given amount.
    """
    try:
        db=get_db()
        user_doc_ref = db.collection(user_collection).document(user_id)
        wallet_doc_ref = user_doc_ref.collection(wallet_collection).document(user_id)
        wallet_doc = wallet_doc_ref.get()
        current_balance = wallet_doc.to_dict().get("balance", 0) if wallet_doc.exists else 0
        new_balance = current_balance + amount

        wallet_doc_ref.set({
            "balance": new_balance,
            "transactions": array_union({
                "transaction_id": transaction_id,
                "amount": amount,
                "top_up_time": transaction_time,
                "phone_number": phone_number,
                "first_name": first_name,
                "last_name": last_name

            })
        }, merge=True)

        print(f"Wallet updated successfully. New balance: {new_balance}")
        return new_balance
    except Exception as e:
        logger.debug("Error" + (str(e)))
        raise Exception(e)

@limits(calls=100, period=ONE_MINUTE)
def fetch_patient_balance(user_id: str):
    """
    Fetch the current wallet balance for a specific patient/user.
    Parameters:
        user_id (str): The unique identifier of the patient/user.
    Returns:
        dict: A dictionary containing the user's current balance and transaction history.
              Returns None if the user or wallet is not found.
    """
    try:
        db=get_db()
        # Reference to the user's document and wallet sub-collection
        user_doc_ref = db.collection(user_collection).document(user_id)
        wallet_doc_ref = user_doc_ref.collection(wallet_collection).document(user_id)
        wallet_doc = wallet_doc_ref.get()
        if wallet_doc.exists:
            wallet_data = wallet_doc.to_dict()
            current_balance = wallet_data.get("Balance", 0)
            transactions = wallet_data.get("transactions", [])
            print(f"Balance fetched successfully. Current balance: {current_balance}")
            return {
                "Balance": current_balance,
                "Transactions": transactions
            }
        else:
            print(f"Wallet for user_id {user_id} not found.")
            return None

    except Exception as e:
        print(f"Error fetching wallet balance: {e}")
        return None

@limits(calls=100, period=ONE_MINUTE) 
def check_user_exist(user_id: str):
        """
        Check if user exists in the backend.
        Parameters:
            user_id (str): The unique identifier of the patient/user.
        Returns:
            bool: whether the user can be found or None if not.
        """
        try:
            db=get_db()
            user_doc_ref = db.collection(user_collection).document(user_id)
            user_doc = user_doc_ref.get()

            if not user_doc.exists:
                return None
            return True
        except Exception as e:
            print(f"Error fetching wallet balance: {e}")
            return None
        

@limits(calls=100, period=ONE_MINUTE)
def update_therapist_balance(user_id: str, transaction_id: str, amount: float, transaction_type: str):
    """
    Fetch and update the user's wallet balance, tracking various metrics like transaction count,
    monthly earnings, total earnings, and session counts.
    """
    try:
        # Parse the transaction time into a datetime object
        transaction_time = datetime.now().isoformat()  # Use ISO 8601 format
        transaction_month = datetime.now().strftime("%Y-%m")  # Example: "2024-12"

        db = get_db()
        user_doc_ref = db.collection(user_collection).document(user_id)
        wallet_doc_ref = user_doc_ref.collection(wallet_collection).document(user_id)
        wallet_doc = wallet_doc_ref.get()
        wallet_data = wallet_doc.to_dict() if wallet_doc.exists else {}

        # Retrieve or initialize wallet data
        current_balance = wallet_data.get("balance", 0)
        total_earnings = wallet_data.get("total_earnings", 0)
        transaction_count = wallet_data.get("transaction_count", 0)
        monthly_data = wallet_data.get("monthly_data", {}).get(transaction_month, {
            "monthly_earnings": 0,
            "monthly_session_count": 0
        })

        # Handle transaction type logic
        if transaction_type == "withdrawal":
            if amount > current_balance:
                raise ValueError("Insufficient balance for withdrawal.")
            new_balance = current_balance - amount
        elif transaction_type in ["credit", "session_payment"]:
            new_balance = current_balance + amount
            total_earnings += amount
            monthly_data["monthly_earnings"] += amount

            # Update session count if it's a session payment
            if transaction_type == "session_payment":
                monthly_data["monthly_session_count"] += 1
        else:
            raise ValueError("Invalid transaction type. Must be 'credit', 'withdrawal', or 'session_payment'.")

        # Increment the total transaction count
        transaction_count += 1

        # Update wallet document with new data
        wallet_doc_ref.set({
            "balance": new_balance,
            "total_earnings": total_earnings,
            "transaction_count": transaction_count,
            "monthly_data": {
                **wallet_data.get("monthly_data", {}),
                transaction_month: monthly_data
            },
            "transactions": array_union({
                "transaction_id": transaction_id,
                "amount": amount,
                "transaction_time": transaction_time,
                "transaction_type": transaction_type
            })
        }, merge=True)

        print(f"Wallet updated successfully. New balance: {new_balance}")
        return {
            "new_balance": new_balance,
            "total_earnings": total_earnings,
            "transaction_count": transaction_count,
            "monthly_data": monthly_data,
            "transaction_id": transaction_id
        }

    except Exception as e:
        logger.debug(f"Error: {str(e)}")
        raise

@limits(calls=100, period=ONE_MINUTE)
def fetch_therapist_wallet_info(user_id: str):
    """
    Fetch all wallet information for the given user, including balance, transactions, 
    total earnings, and monthly statistics.
    """
    try:
        db = get_db()
        user_doc_ref = db.collection(user_collection).document(user_id)
        wallet_doc_ref = user_doc_ref.collection(wallet_collection).document(user_id)
        wallet_doc = wallet_doc_ref.get()

        # Fetch wallet data or use default values if the document does not exist
        wallet_data = wallet_doc.to_dict() if wallet_doc.exists else {}
        balance = wallet_data.get("balance", 0)
        total_earnings = wallet_data.get("total_earnings", 0)
        transaction_count = wallet_data.get("transaction_count", 0)
        monthly_data = wallet_data.get("monthly_data", {"monthly_earnings": 0,
            "monthly_session_count": 0})
        transactions = wallet_data.get("transactions", [])

        # Return the data with default values if necessary
        return {
            "balance": balance,
            "total_earnings": total_earnings,
            "transaction_count": transaction_count,
            "monthly_data": monthly_data,
            "transactions": transactions
        }
    except Exception as e:
        logger.debug(f"Error fetching wallet info: {str(e)}")
        raise
    

@limits(calls=100, period=ONE_MINUTE)
def create_calendar_event(
    event_name: str,
    start_time: datetime,
    end_time: datetime,
    description: str,
    location: str,
    therapist_email: str,
    frequency: str,
    repeating_session: bool,
    therapist_name: str,
    therapist_id: str,
    patient_id: str,
    meeting_link: str,
    patient_name: str,
    recipient_email: str
) -> str:
    """
    Create a new calendar event for a therapy session.
    
    Args:
        event_name: Name of the event
        start_time: Start time of the session
        end_time: End time of the session
        description: Description of the session
        location: Location of the session
        therapist_email: Email of the therapist
        frequency: Frequency of recurring sessions (daily, weekly, monthly)
        repeating_session: Whether this is a recurring session
        therapist_name: Name of the therapist
        therapist_id: ID of the therapist
        patient_id: ID of the patient
        meeting_link: URL for virtual meeting
        patient_name: Name of the patient
        recipient_email: Email of the recipient for notifications
    
    Returns:
        str: The ID of the created event
    """
    db = get_db()
    
    # Generate a unique event ID
    event_id = str(uuid.uuid4())
    
    # Create the event data
    event_data = {
        'event_id': event_id,
        'event_name': event_name,
        'start_time': start_time,
        'end_time': end_time,
        'description': description,
        'location': location,
        'therapist_email': therapist_email,
        'therapist_name': therapist_name,
        'therapist_id': therapist_id,
        'patient_id': patient_id,
        'patient_name': patient_name,
        'recipient_email': recipient_email,
        'meeting_link': meeting_link,
        'frequency': frequency,
        'repeating_session': repeating_session,
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow(),
        'status': 'active'
    }
    
    # Create references to the necessary collections
    therapist_doc_ref = db.collection(user_collection).document(therapist_id)
    calendar_doc_ref = therapist_doc_ref.collection(calendar_collection).document(event_id)
    
    # Store the event in Firestore
    calendar_doc_ref.set(event_data)
    
    # Update the therapist's document with the latest event
    therapist_doc_ref.set({
        'last_event_created': datetime.utcnow(),
        'total_events': firestore.Increment(1)
    }, merge=True)
    
    return event_id

@limits(calls=100, period=ONE_MINUTE)
def get_calendar_event(therapist_id: str, event_id: str) -> Optional[Dict]:
    """
    Retrieve a specific calendar event.
    
    Args:
        therapist_id: ID of the therapist
        event_id: ID of the event to retrieve
    
    Returns:
        Optional[Dict]: The event data if found, None otherwise
    """
    db = get_db()
    event_doc = db.collection(user_collection).document(therapist_id)\
                  .collection(calendar_collection).document(event_id).get()
    
    return event_doc.to_dict() if event_doc.exists else None

@limits(calls=100, period=ONE_MINUTE)
def get_therapist_calendar_events(
    therapist_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> List[Dict]:
    """
    Retrieve all calendar events for a therapist within a date range.
    
    Args:
        therapist_id: ID of the therapist
        start_date: Optional start date filter
        end_date: Optional end date filter
    
    Returns:
        List[Dict]: List of event data
    """
    db = get_db()
    query = db.collection(user_collection).document(therapist_id)\
             .collection(calendar_collection)
    
    if start_date:
        query = query.where('start_time', '>=', start_date)
    if end_date:
        query = query.where('start_time', '<=', end_date)
    
    events = query.stream()
    return [event.to_dict() for event in events]

@limits(calls=100, period=ONE_MINUTE)
def update_calendar_event(
    therapist_id: str,
    event_id: str,
    updates: Dict
) -> bool:
    """
    Update an existing calendar event.
    
    Args:
        therapist_id: ID of the therapist
        event_id: ID of the event to update
        updates: Dictionary containing the fields to update
    
    Returns:
        bool: True if update was successful, False otherwise
    """
    db = get_db()
    event_ref = db.collection(user_collection).document(therapist_id)\
                  .collection(calendar_collection).document(event_id)
    
    # Add updated_at timestamp
    updates['updated_at'] = datetime.utcnow()
    
    try:
        event_ref.update(updates)
        return True
    except Exception:
        return False

@limits(calls=100, period=ONE_MINUTE)
def delete_calendar_event(therapist_id: str, event_id: str) -> bool:
    """
    Delete a calendar event.
    
    Args:
        therapist_id: ID of the therapist
        event_id: ID of the event to delete
    
    Returns:
        bool: True if deletion was successful, False otherwise
    """
    db = get_db()
    event_ref = db.collection(user_collection).document(therapist_id)\
                  .collection(calendar_collection).document(event_id)
    
    try:
        event_ref.delete()
        # Update the therapist's document
        db.collection(user_collection).document(therapist_id).set({
            'total_events': firestore.Increment(-1)
        }, merge=True)
        return True
    except Exception:
        return False

@limits(calls=100, period=ONE_MINUTE)
def verify_admin(auth_token):
    db = get_db()
    try:
        # Verify the token first
        decoded_token = auth.verify_id_token(auth_token)
        
        # Get the user's UUID from the decoded token
        uuid = decoded_token['uid']
        
        # Now query the admins collection using the UUID
        admins_ref = db.collection("admins")
        query = admins_ref.where(filter=FieldFilter("uuid", "==", uuid))
        results = query.stream()
        
        return results, uuid
    except auth.InvalidIdTokenError:
        raise Exception("Invalid auth token")
    except auth.ExpiredIdTokenError:
        raise Exception("Expired auth token")
    except Exception as e:
        raise Exception(f"Verification failed: {str(e)}")

@limits(calls=100, period=ONE_MINUTE)
def fetch_admin(auth_token):
    db = get_db()
    try:
        # Verify the token first
        decoded_token = auth.verify_id_token(auth_token)
        
        # Get the user's UUID from the decoded token
        uuid = decoded_token['uid']
        
        # Now query the admins collection using the UUID
        admins_ref = db.collection("admins")
        query = admins_ref.where(filter=FieldFilter("uuid", "==", uuid))
        results = query.stream()
        # logger.info(admin_address)
        # Extract the document if found
        admin_data = None
        for doc in results:
            admin_data = doc.to_dict()  # Get the document as a dictionary
        # logger.info(admin_data)
        if admin_data:
            # Return the desired structure if admin exists
            return {
                "auth_token": admin_data.get("auth_token"),
                "key": admin_data.get("key"),
                "name": admin_data.get("name")
            }
        else:
            # Return None or appropriate error if no document is found
            return {"error": "Admin not found"}
    except Exception as e:
        # Log or handle error appropriately
        print(f"Error fetching admin: {e}")
        return {"error": "Failed to fetch admin"}