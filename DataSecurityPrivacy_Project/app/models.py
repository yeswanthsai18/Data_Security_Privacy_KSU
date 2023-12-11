from app import db
from cryptography.fernet import Fernet
from cryptography.fernet import InvalidToken
from flask_login import UserMixin

# Generate a key for encryption and create a cipher suite
key = Fernet.generate_key()
cipher_suite = Fernet(key)

# Function to encrypt data
def data_encryption(data):
    # Convert data to string and encrypt using the cipher suite
    data_str = str(data)
    ciphered_data = cipher_suite.encrypt(data_str.encode())
    return ciphered_data

# Function to decrypt data
def data_decryption(data):
    try:
        # Decrypt data using the cipher suite
        deciphered_data = cipher_suite.decrypt(data)
        # Assuming the data is stored as utf-8, decode and return
        return deciphered_data.decode('utf-8')
    except (InvalidToken, UnicodeDecodeError):
        # Handle decryption errors, return None
        return None

# Model for HealthRecord table
class HealthRecord(db.Model):
    __tablename__ = 'HealthRecord'

    id = db.Column(db.Integer, primary_key=True)
    First_name = db.Column(db.String(100))
    Last_name = db.Column(db.String(100))
    age = db.Column(db.Integer)
    Gender = db.Column(db.String(20))
    weight = db.Column(db.Float)
    height = db.Column(db.Float)
    health_history = db.Column(db.String(100))

# Model for User table
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.LargeBinary)  # Change the column type to LargeBinary for storing encrypted data
    group = db.Column(db.String(1))  # Assuming 'H' or 'R' as the group values

    # Method to set the password for the user
    def password_set(self, password):
        # Encrypt the password and store in the 'password' column
        encrypted_password = data_encryption(password)
        self.password = encrypted_password

    # Method to check if the provided password matches the stored encrypted password
    def password_check(self, password):
        # Decrypt the stored password and compare with the provided password
        decrypted_password = data_decryption(self.password)
        return password == decrypted_password
