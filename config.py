import logging
import os

DEBUG_LEVEL = logging.DEBUG if bool(os.environ.get("DEBUG", False)) else logging.INFO
logging.basicConfig(level=DEBUG_LEVEL,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M')

SQL_ALCH_DATABASE = None
BASE_DIR = os.getcwd()
#
#   ===================================
#   DATABASE_DIALECT: postgresql+pg8000
#   DATABASE_USERL: username
#   DATABASE_PASS: password
#   DATABASE_URL: ip(:port)/database
#   ===================================
#
if os.environ.get('DATABASE_DIALECT') and os.environ.get('DATABASE_USER') and os.environ.get('DATABASE_PASS') and os.environ.get('DATABASE_IP') and os.environ.get('DATABASE_NAME'):
        SQL_ALCH_DATABASE = f"{os.environ.get('DATABASE_DIALECT')}://{os.environ.get('DATABASE_USER')}:{os.environ.get('DATABASE_PASS')}@{os.environ.get('DATABASE_IP')}/{os.environ.get('DATABASE_NAME')}"
        logging.debug(f"[DATABASE] Using external database with dialect {os.environ.get('DATABASE_DIALECT')}")
        logging.debug(f"Using connection: {SQL_ALCH_DATABASE}")
else:
    logging.debug('[DATABASE] Either DATABASE_DIALECT, DATABASE_USER, DATABASE_PASS, DATABASE_IP or DATABASE_NAME is missing')
    logging.debug('[DATABASE] Using default sqlite database')
    pass
SQLALCHEMY_DATABASE_URI = SQL_ALCH_DATABASE or 'sqlite:///' + os.path.join(BASE_DIR, 'rss.db')
    