import base64
import math
import os
import RNS
import time
import atexit
import base64
from .vendor import umsgpack as umsgpack
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.fernet import Fernet

cio_default_backend = default_backend()

class Identity:
    """
    This class is used to manage identities in Reticulum. It provides methods
    for encryption, decryption, signatures and verification, and is the basis
    for all encrypted communication over Reticulum networks.

    :param create_keys: Specifies whether new encryption and signing keys should be generated.
    """

    CURVE = "Curve25519"
    """
    The curve used for Elliptic Curve DH key exchanges
    """

    KEYSIZE     = 256*2
    """
    X25519 key size in bits. A complete key is the concatenation of a 256 bit encryption key, and a 256 bit signing key.
    """   

    # Non-configurable constants
    FERNET_VERSION   = 0x80
    FERNET_OVERHEAD  = 54     # In bytes
    AES128_BLOCKSIZE = 16     # In bytes
    HASHLENGTH  = 256         # In bits
    SIGLENGTH   = KEYSIZE     # In bits

    TRUNCATED_HASHLENGTH = RNS.Reticulum.TRUNCATED_HASHLENGTH
    """
    Constant specifying the truncated hash length (in bits) used by Reticulum
    for addressable hashes and other purposes. Non-configurable.
    """

    # Storage
    known_destinations = {}

    @staticmethod
    def remember(packet_hash, destination_hash, public_key, app_data = None):
        if len(public_key) != Identity.KEYSIZE//8:
            raise TypeError("Can't remember "+RNS.prettyhexrep(destination_hash)+", the public key size of "+str(len(public_key))+" is not valid.", RNS.LOG_ERROR)
        else:
            Identity.known_destinations[destination_hash] = [time.time(), packet_hash, public_key, app_data]


    @staticmethod
    def recall(destination_hash):
        """
        Recall identity for a destination hash.

        :param destination_hash: Destination hash as *bytes*.
        :returns: An :ref:`RNS.Identity<api-identity>` instance that can be used to create an outgoing :ref:`RNS.Destination<api-destination>`, or *None* if the destination is unknown.
        """
        if destination_hash in Identity.known_destinations:
            identity_data = Identity.known_destinations[destination_hash]
            identity = Identity(create_keys=False)
            identity.load_public_key(identity_data[2])
            identity.app_data = identity_data[3]
            return identity
        else:
            return None

    @staticmethod
    def recall_app_data(destination_hash):
        """
        Recall last heard app_data for a destination hash.

        :param destination_hash: Destination hash as *bytes*.
        :returns: *Bytes* containing app_data, or *None* if the destination is unknown.
        """
        if destination_hash in Identity.known_destinations:
            app_data = Identity.known_destinations[destination_hash][3]
            return app_data
        else:
            return None

    @staticmethod
    def save_known_destinations():
        try:
            storage_known_destinations = {}
            if os.path.isfile(RNS.Reticulum.storagepath+"/known_destinations"):
                try:
                    file = open(RNS.Reticulum.storagepath+"/known_destinations","rb")
                    storage_known_destinations = umsgpack.load(file)
                    file.close()
                except:
                    pass

            for destination_hash in storage_known_destinations:
                if not destination_hash in Identity.known_destinations:
                    Identity.known_destinations[destination_hash] = storage_known_destinations[destination_hash]

            RNS.log("Saving known destinations to storage...", RNS.LOG_VERBOSE)
            file = open(RNS.Reticulum.storagepath+"/known_destinations","wb")
            umsgpack.dump(Identity.known_destinations, file)
            file.close()
            RNS.log("Done saving known destinations to storage", RNS.LOG_VERBOSE)
        except Exception as e:
            RNS.log("Error while saving known destinations to disk, the contained exception was: "+str(e), RNS.LOG_ERROR)

    @staticmethod
    def load_known_destinations():
        if os.path.isfile(RNS.Reticulum.storagepath+"/known_destinations"):
            try:
                file = open(RNS.Reticulum.storagepath+"/known_destinations","rb")
                Identity.known_destinations = umsgpack.load(file)
                file.close()
                RNS.log("Loaded "+str(len(Identity.known_destinations))+" known destination from storage", RNS.LOG_VERBOSE)
            except:
                RNS.log("Error loading known destinations from disk, file will be recreated on exit", RNS.LOG_ERROR)
        else:
            RNS.log("Destinations file does not exist, no known destinations loaded", RNS.LOG_VERBOSE)

    @staticmethod
    def full_hash(data):
        """
        Get a SHA-256 hash of passed data.

        :param data: Data to be hashed as *bytes*.
        :returns: SHA-256 hash as *bytes*
        """
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(data)

        return digest.finalize()

    @staticmethod
    def truncated_hash(data):
        """
        Get a truncated SHA-256 hash of passed data.

        :param data: Data to be hashed as *bytes*.
        :returns: Truncated SHA-256 hash as *bytes*
        """
        return Identity.full_hash(data)[:(Identity.TRUNCATED_HASHLENGTH//8)]

    @staticmethod
    def get_random_hash():
        """
        Get a random SHA-256 hash.

        :param data: Data to be hashed as *bytes*.
        :returns: Truncated SHA-256 hash of random data as *bytes*
        """
        return Identity.truncated_hash(os.urandom(10))

    @staticmethod
    def validate_announce(packet):
        if packet.packet_type == RNS.Packet.ANNOUNCE:
            RNS.log("Validating announce from "+RNS.prettyhexrep(packet.destination_hash), RNS.LOG_DEBUG)
            destination_hash = packet.destination_hash
            public_key = packet.data[:Identity.KEYSIZE//8]
            random_hash = packet.data[Identity.KEYSIZE//8:Identity.KEYSIZE//8+10]
            signature = packet.data[Identity.KEYSIZE//8+10:Identity.KEYSIZE//8+10+Identity.KEYSIZE//8]
            app_data = b""
            if len(packet.data) > Identity.KEYSIZE//8+10+Identity.KEYSIZE//8:
                app_data = packet.data[Identity.KEYSIZE//8+10+Identity.KEYSIZE//8:]

            signed_data = destination_hash+public_key+random_hash+app_data

            if not len(packet.data) > Identity.KEYSIZE//8+10+Identity.KEYSIZE//8:
                app_data = None

            announced_identity = Identity(create_keys=False)
            announced_identity.load_public_key(public_key)

            if announced_identity.pub != None and announced_identity.validate(signature, signed_data):
                RNS.Identity.remember(packet.get_hash(), destination_hash, public_key, app_data)
                RNS.log("Stored valid announce from "+RNS.prettyhexrep(destination_hash), RNS.LOG_DEBUG)
                del announced_identity
                return True
            else:
                RNS.log("Received invalid announce", RNS.LOG_DEBUG)
                del announced_identity
                return False

    @staticmethod
    def exit_handler():
        Identity.save_known_destinations()


    @staticmethod
    def from_bytes(prv_bytes):
        """
        Create a new :ref:`RNS.Identity<api-identity>` instance from *bytes* of private key.
        Can be used to load previously created and saved identities into Reticulum.

        :param prv_bytes: The *bytes* of private a saved private key. **HAZARD!** Never use this to generate a new key by feeding random data in prv_bytes.
        :returns: A :ref:`RNS.Identity<api-identity>` instance, or *None* if the *bytes* data was invalid.
        """
        identity = Identity(create_keys=False)
        if identity.load_private_key(prv_bytes):
            return identity
        else:
            return None


    @staticmethod
    def from_file(path):
        """
        Create a new :ref:`RNS.Identity<api-identity>` instance from a file.
        Can be used to load previously created and saved identities into Reticulum.

        :param path: The full path to the saved :ref:`RNS.Identity<api-identity>` data
        :returns: A :ref:`RNS.Identity<api-identity>` instance, or *None* if the loaded data was invalid.
        """
        identity = Identity(create_keys=False)
        if identity.load(path):
            return identity
        else:
            return None

    def to_file(self, path):
        """
        Saves the identity to a file. This will write the private key to disk,
        and anyone with access to this file will be able to decrypt all
        communication for the identity. Be very careful with this method.

        :param path: The full path specifying where to save the identity.
        :returns: True if the file was saved, otherwise False.
        """
        try:
            with open(path, "wb") as key_file:
                key_file.write(self.get_private_key())
                return True
            return False
        except Exception as e:
            RNS.log("Error while saving identity to "+str(path), RNS.LOG_ERROR)
            RNS.log("The contained exception was: "+str(e))

    def __init__(self,create_keys=True):
        # Initialize keys to none
        self.prv           = None
        self.prv_bytes     = None
        self.sig_prv       = None
        self.sig_prv_bytes = None

        self.pub           = None
        self.pub_bytes     = None
        self.sig_pub       = None
        self.sig_pub_bytes = None

        self.hash          = None
        self.hexhash       = None

        if create_keys:
            self.create_keys()

    def create_keys(self):
        self.prv           = X25519PrivateKey.generate()
        self.prv_bytes     = self.prv.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )

        self.sig_prv       = Ed25519PrivateKey.generate()
        self.sig_prv_bytes = self.sig_prv.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )

        self.pub           = self.prv.public_key()
        self.pub_bytes     = self.pub.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )

        self.sig_pub       = self.sig_prv.public_key()
        self.sig_pub_bytes = self.sig_pub.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )

        self.update_hashes()

        RNS.log("Identity keys created for "+RNS.prettyhexrep(self.hash), RNS.LOG_VERBOSE)

    def get_private_key(self):
        """
        :returns: The private key as *bytes*
        """
        return self.prv_bytes+self.sig_prv_bytes

    def get_public_key(self):
        """
        :returns: The public key as *bytes*
        """
        return self.pub_bytes+self.sig_pub_bytes

    def load_private_key(self, prv_bytes):
        """
        Load a private key into the instance.

        :param prv_bytes: The private key as *bytes*.
        :returns: True if the key was loaded, otherwise False.
        """
        try:
            self.prv_bytes     = prv_bytes[:Identity.KEYSIZE//8//2]
            self.prv           = X25519PrivateKey.from_private_bytes(self.prv_bytes)
            self.sig_prv_bytes = prv_bytes[Identity.KEYSIZE//8//2:]
            self.sig_prv       = Ed25519PrivateKey.from_private_bytes(self.sig_prv_bytes)
            
            self.pub           = self.prv.public_key()
            self.pub_bytes     = self.pub.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw
            )

            self.sig_pub       = self.sig_prv.public_key()
            self.sig_pub_bytes = self.sig_pub.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw
            )

            self.update_hashes()

            return True

        except Exception as e:
            raise e
            RNS.log("Failed to load identity key", RNS.LOG_ERROR)
            RNS.log("The contained exception was: "+str(e), RNS.LOG_ERROR)
            return False

    def load_public_key(self, pub_bytes):
        """
        Load a public key into the instance.

        :param pub_bytes: The public key as *bytes*.
        :returns: True if the key was loaded, otherwise False.
        """
        try:
            self.pub_bytes     = pub_bytes[:Identity.KEYSIZE//8//2]
            self.sig_pub_bytes = pub_bytes[Identity.KEYSIZE//8//2:]

            self.pub           = X25519PublicKey.from_public_bytes(self.pub_bytes)
            self.sig_pub       = Ed25519PublicKey.from_public_bytes(self.sig_pub_bytes)

            self.update_hashes()
        except Exception as e:
            RNS.log("Error while loading public key, the contained exception was: "+str(e), RNS.LOG_ERROR)

    def update_hashes(self):
        self.hash = Identity.truncated_hash(self.get_public_key())
        self.hexhash = self.hash.hex()

    def load(self, path):
        try:
            with open(path, "rb") as key_file:
                prv_bytes = key_file.read()
                return self.load_private_key(prv_bytes)
            return False
        except Exception as e:
            RNS.log("Error while loading identity from "+str(path), RNS.LOG_ERROR)
            RNS.log("The contained exception was: "+str(e))

    def get_salt(self):
        return self.hash

    def get_context(self):
        return None

    def encrypt(self, plaintext):
        """
        Encrypts information for the identity.

        :param plaintext: The plaintext to be encrypted as *bytes*.
        :returns: Ciphertext token as *bytes*.
        :raises: *KeyError* if the instance does not hold a public key.
        """
        if self.pub != None:
            ephemeral_key = X25519PrivateKey.generate()
            ephemeral_pub_bytes = ephemeral_key.public_key().public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw
            )

            shared_key = ephemeral_key.exchange(self.pub)
            
            # TODO: Improve this re-allocation of HKDF
            derived_key = HKDF(
                algorithm=hashes.SHA256(),
                length=32,
                salt=self.get_salt(),
                info=self.get_context(),
                backend=cio_default_backend,
            ).derive(shared_key)

            fernet = Fernet(base64.urlsafe_b64encode(derived_key))
            ciphertext = base64.urlsafe_b64decode(fernet.encrypt(plaintext))
            token = ephemeral_pub_bytes+ciphertext

            return token
        else:
            raise KeyError("Encryption failed because identity does not hold a public key")


    def decrypt(self, ciphertext_token):
        """
        Decrypts information for the identity.

        :param ciphertext: The ciphertext to be decrypted as *bytes*.
        :returns: Plaintext as *bytes*, or *None* if decryption fails.
        :raises: *KeyError* if the instance does not hold a private key.
        """
        if self.prv != None:
            if len(ciphertext_token) > Identity.KEYSIZE//8//2:
                plaintext = None
                try:
                    peer_pub_bytes = ciphertext_token[:Identity.KEYSIZE//8//2]
                    peer_pub = X25519PublicKey.from_public_bytes(peer_pub_bytes)

                    shared_key = self.prv.exchange(peer_pub)

                    # TODO: Improve this re-allocation of HKDF
                    derived_key = HKDF(
                        algorithm=hashes.SHA256(),
                        length=32,
                        salt=self.get_salt(),
                        info=self.get_context(),
                        backend=cio_default_backend,
                    ).derive(shared_key)

                    fernet = Fernet(base64.urlsafe_b64encode(derived_key))
                    ciphertext = ciphertext_token[Identity.KEYSIZE//8//2:]
                    plaintext = fernet.decrypt(base64.urlsafe_b64encode(ciphertext))

                except Exception as e:
                    RNS.log("Decryption by "+RNS.prettyhexrep(self.hash)+" failed: "+str(e), RNS.LOG_DEBUG)
                    
                return plaintext;
            else:
                RNS.log("Decryption failed because the token size was invalid.", RNS.LOG_DEBUG)
                return None
        else:
            raise KeyError("Decryption failed because identity does not hold a private key")


    def sign(self, message):
        """
        Signs information by the identity.

        :param message: The message to be signed as *bytes*.
        :returns: Signature as *bytes*.
        :raises: *KeyError* if the instance does not hold a private key.
        """
        if self.sig_prv != None:
            try:
                return self.sig_prv.sign(message)    
            except Exception as e:
                RNS.log("The identity "+str(self)+" could not sign the requested message. The contained exception was: "+str(e), RNS.LOG_ERROR)
                raise e 
        else:
            raise KeyError("Signing failed because identity does not hold a private key")

    def validate(self, signature, message):
        """
        Validates the signature of a signed message.

        :param signature: The signature to be validated as *bytes*.
        :param message: The message to be validated as *bytes*.
        :returns: True if the signature is valid, otherwise False.
        :raises: *KeyError* if the instance does not hold a public key.
        """
        if self.pub != None:
            try:
                self.sig_pub.verify(signature, message)
                return True
            except Exception as e:
                return False
        else:
            raise KeyError("Signature validation failed because identity does not hold a public key")

    def prove(self, packet, destination=None):
        signature = self.sign(packet.packet_hash)
        if RNS.Reticulum.should_use_implicit_proof():
            proof_data = signature
        else:
            proof_data = packet.packet_hash + signature
        
        if destination == None:
            destination = packet.generate_proof_destination()

        proof = RNS.Packet(destination, proof_data, RNS.Packet.PROOF, attached_interface = packet.receiving_interface)
        proof.send()

    def __str__(self):
        return RNS.prettyhexrep(self.hash)
