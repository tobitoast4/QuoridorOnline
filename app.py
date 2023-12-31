from flask import Flask, request, render_template, redirect, url_for, session, make_response, session, flash, get_flashed_messages
from flask_login import login_user, LoginManager, login_required, logout_user, current_user

import user
import utils
import lobby
from quoridor.game import Game


app = Flask(__name__)
app.config["SECRET_KEY"] = "asdf7878"

login_manager = LoginManager()
login_manager.init_app(app)

lobby_manager = lobby.LobbyManager()


@login_manager.user_loader
def load_user(user_id):
    the_user = user.User()
    the_user.id = user_id
    the_user.name = session['user_name']
    return the_user


@app.route("/")
def home():
    the_user = log_in_user()
    return render_template("home.html", user=the_user)


@app.route("/lobby/")
@app.route("/lobby/<string:lobby_id>")
def lobby(lobby_id=None):
    the_user = log_in_user()
    if lobby_id is None:
        # create new lobby
        new_lobby = lobby_manager.create_new_lobby()
        return redirect(f"/lobby/{new_lobby.lobby_id}")
    else:
        # join lobby
        the_lobby = lobby_manager.get_lobby(lobby_id)
        return render_template("lobby.html", lobby=the_lobby, user=the_user)


@app.route("/get_lobby/", methods=['POST'])
@app.route("/get_lobby/<string:lobby_id>", methods=['POST'])
def get_lobby(lobby_id=None):
    if lobby_id is None:
        return {"error": f"lobby with id {lobby_id} does not exist."}, 502
    user_sending_the_request = user.get_user_from_dict(request.json)
    the_lobby = lobby_manager.get_lobby(lobby_id)
    if the_lobby is not None:
        if the_lobby.game is None:  # game not started yet
            lobby_manager.add_player_to_lobby(lobby_id, user_sending_the_request)
            return the_lobby.to_json(), 200
        else:  # game started
            return {"game": f"http://127.0.0.1:5009/game/{lobby_id}"}
    else:
        return {"error": f"lobby with id {lobby_id} does not exist."}, 502


@app.route("/start_game/<string:lobby_id>", methods=['POST'])
def start_game(lobby_id):
    the_lobby = lobby_manager.get_lobby(lobby_id)
    the_lobby.start_game()
    return {"status": "game started"}, 200


@app.route("/game/<string:lobby_id>")
def game(lobby_id):
    the_user = log_in_user()
    the_lobby = lobby_manager.get_lobby(lobby_id)
    return render_template("game.html", user=the_user, lobby=the_lobby)


@app.route("/game_move_player/<string:lobby_id>", methods=['POST'])
def game_move_player(lobby_id):
    the_lobby = lobby_manager.get_lobby(lobby_id)
    the_game = the_lobby.game
    print(the_game.game_data)
    request_data = request.json
    print(request_data)
    the_game.move_player(request_data["user_id"],
                         request_data["new_field_col_num"],
                         request_data["new_field_row_num"])
    return {"status": "player moved"}, 200


@app.route("/game_place_wall/<string:lobby_id>", methods=['POST'])
def game_place_wall(lobby_id):
    print(request.json)


@app.route("/get_game_data/<string:lobby_id>", methods=['POST'])
def get_game_data(lobby_id):
    the_lobby = lobby_manager.get_lobby(lobby_id)
    the_game = the_lobby.game
    return the_game.game_data


def log_in_user():
    if "user_id" in session:
        # user is already logged in
        the_user = user.User()
        the_user.id = session['user_id']
        the_user.name = session['user_name']
        return the_user
    else:
        # user not registered yet, create new
        new_user = user.User()
        session['user_id'] = new_user.id
        session['user_name'] = new_user.name
        return new_user


if __name__ == '__main__':
    # app.run(host="0.0.0.0") # use me for prod
    app.run(host="127.0.0.1", port=5009, debug=True)