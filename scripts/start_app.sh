#!/bin/sh
#
# Start the uvicorn server for our FastAPI app.
#
# NOTE: We do not expect our app to get much traffic so using a single
#       asyncio based process should be good enough to handle all the
#       traffic it will receive.
#
SCRIPT_PATH="$(readlink -f "${BASH_SOURCE}")"
SCRIPT_DIR="$(dirname "${SCRIPT_PATH}")"
INSTALL_DIR="$(dirname "${SCRIPT_DIR}")"
echo "Script path is ${SCRIPT_PATH}"
echo "Script dir is ${SCRIPT_DIR}"
echo "Install dir is ${INSTALL_DIR}"

cd "${INSTALL_DIR}"
. "${INSTALL_DIR}/venv/bin/activate"
uvicorn --host 127.0.0.1 --port 8000 app.main:app
