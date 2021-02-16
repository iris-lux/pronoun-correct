from app import app

if __name__ == '__main__':
    app.socketio.run(app.app, debug=True)