import os
import logging
from stem.control import Controller
from stem import process

logging.basicConfig(level=logging.INFO)

def start_tor():
    tor_data_dir = os.path.join(os.getcwd(), "tor_data")
    os.makedirs(tor_data_dir, exist_ok=True)
    
    try:
        process.launch_tor_with_config(
            config={
                'SocksPort': '9050',
                'ControlPort': '9051',
                'DataDirectory': tor_data_dir,
                'HiddenServiceDir': os.path.join(tor_data_dir, 'hidden_service'),
                'HiddenServicePort': f'80 127.0.0.1:5000',
                'HiddenServicePort': f'{9000} 127.0.0.1:9000',
            }
        )
        logging.info("Tor started successfully.")
    except Exception as e:
        logging.error(f"Failed to start Tor: {e}")

def get_onion_address():
    with Controller.from_port(port=9051) as controller:
        controller.authenticate()
        return controller.get_hidden_service(os.path.join(os.getcwd(), "tor_data/hidden_service")).hostname
