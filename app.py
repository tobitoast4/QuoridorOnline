from flask import Flask, request, render_template, redirect, url_for, session, make_response, session, flash
from flask_login import login_user, LoginManager, login_required, logout_user, current_user
from werkzeug.exceptions import HTTPException
import os, json

import user
import lobby as lobby_manager
import utils

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("QUORIDOR_SECRET_KEY")

login_manager = LoginManager()
login_manager.init_app(app)


@app.errorhandler(Exception)
def handle_exception(e):
    # pass through HTTP errors
    if isinstance(e, HTTPException):
        return e
    if isinstance(e, json.decoder.JSONDecodeError):
        return {"error": f"JSONDecodeError: {str(e)}"}, 500
    return {"error": str(e)}, 500


@login_manager.user_loader
def load_user(user_id):
    the_user = user.User()
    the_user.id = user_id
    the_user.name = session['user_name']
    return the_user


@app.after_request
def handle_options(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-Requested-With"
    return response


@app.route("/", methods=['GET'])
def home():
    the_user = log_in_user()
    return render_template("home.html", user=the_user, server_url=request.url_root)


@app.route("/local", methods=['GET'])
def local():
    amount_players = request.args.get('amount_players', default=2, type=int)
    return render_template("game_local.html", amount_players=amount_players)


@app.route("/how-to-play", methods=['GET'])
def how_to_play():
    return render_template("how_to_play.html")


@app.route("/about", methods=['GET'])
def about():
    return render_template("about.html")


@app.route("/get_random_lobby", methods=['GET'])
def get_random_lobby():
    the_lobby = lobby_manager.get_random_public_lobby()
    return {"lobby_url": f"{request.url_root}lobby/{the_lobby.lobby_id}"}, 200


@app.route("/lobby/", methods=['GET'])
@app.route("/lobby/<string:lobby_id>", methods=['GET'])
def lobby(lobby_id=None):
    the_user = log_in_user()
    if lobby_id is None:
        # create new lobby
        new_lobby = lobby_manager.create_new_lobby(the_user)
        return redirect(f"/lobby/{new_lobby.lobby_id}")
    else:
        # join lobby
        the_lobby = lobby_manager.get_lobby(lobby_id)
        if the_lobby is None:
            flash(f"The lobby with id {lobby_id} does not exist.")
            return redirect("/")
        return render_template("lobby.html", lobby=the_lobby, user=the_user, server_url=request.url_root, colors=utils.COLORS)


@app.route("/get_lobby/", methods=['POST'])
@app.route("/get_lobby/<string:lobby_id>", methods=['POST'])
def get_lobby(lobby_id=None):
    if lobby_id is None:
        flash(f"The lobby with id {lobby_id} does not exist.")
        return redirect("/")
    lobby_manager.check_players_last_seen_time(lobby_id)
    user_sending_the_request = user.get_user_from_dict(request.json)
    the_lobby = lobby_manager.get_lobby(lobby_id)
    if the_lobby is not None:
        if the_lobby.game is None:  # game not started yet
            lobby_manager.add_player_to_lobby(lobby_id, user_sending_the_request)
            return the_lobby.to_json(), 200
        else:  # game started
            return {"game": f"{request.url_root}game/{lobby_id}"}
    else:
        flash(f"The lobby with id {lobby_id} does not exist.")
        return redirect("/")


@app.route("/start_game/<string:lobby_id>", methods=['POST'])
def start_game(lobby_id):
    the_lobby = lobby_manager.get_lobby(lobby_id)
    if session['user_id'] != the_lobby.lobby_owner.id:
        return {"error": "Only the lobby owner can start the game"}
    the_lobby.start_game()
    the_lobby.write_lobby()
    return {"status": "game started"}, 200


@app.route("/change_lobby_visibility/<string:lobby_id>", methods=['POST'])
def change_lobby_visibility(lobby_id):
    the_lobby = lobby_manager.get_lobby(lobby_id)
    if session['user_id'] != the_lobby.lobby_owner.id:
        return {"error": "Only the lobby owner can change the visibility"}
    the_lobby.change_visibility()
    the_lobby.write_lobby()
    if the_lobby.is_private:
        return {"status": "Lobby visibility successfully changed to: private"}, 200
    else:
        return {"status": "Lobby visibility successfully changed to: public"}, 200


@app.route("/change_amount_of_walls_per_player/<string:lobby_id>", methods=['POST'])
def change_amount_of_walls_per_player(lobby_id):
    the_lobby = lobby_manager.get_lobby(lobby_id)
    if session['user_id'] != the_lobby.lobby_owner.id:
        return {"error": "Only the lobby owner can change the amount of walls per player"}
    if the_lobby.game is not None:
        return {"error": "You can not change the amount of walls per player when the game is already running"}
    new_amount = request.json.get("new_amount")
    the_lobby.change_amount_of_walls_of_players(new_amount)
    the_lobby.write_lobby()
    return {"amount_of_walls_per_player": new_amount}, 200  # if all was successful


@app.route("/game/<string:lobby_id>", methods=['GET'])
def game(lobby_id):
    the_user = log_in_user()
    the_lobby = lobby_manager.get_lobby(lobby_id)
    return render_template("game_online.html", user=the_user, lobby=the_lobby, server_url=request.url_root)


@app.route("/game_move_player/<string:lobby_id>", methods=['POST'])
def game_move_player(lobby_id):
    the_lobby = lobby_manager.get_lobby(lobby_id)
    the_game = the_lobby.game
    if request.json.get("user_id") != session['user_id']:
        return {"error": "It's not your turn"}
    else:
        the_game.move_player(request.json.get("user_id"),
                             request.json.get("new_field_col_num"),
                             request.json.get("new_field_row_num"))
    the_lobby.write_lobby()
    return {"status": "player moved"}, 200


@app.route("/game_place_wall/<string:lobby_id>", methods=['POST'])
def game_place_wall(lobby_id):
    the_lobby = lobby_manager.get_lobby(lobby_id)
    the_game = the_lobby.game
    if request.json.get("user_id") != session['user_id']:
        # raise QuoridorOnlineGameError("User can not move another player")
        return {"error": "It is not your turn"}
    else:
        the_game.place_wall(request.json.get("user_id"),
                            request.json.get("col_start"),
                            request.json.get("row_start"),
                            request.json.get("col_end"),
                            request.json.get("row_end"))
    the_lobby.write_lobby()
    return {"status": "wall placed"}, 200


@app.route("/get_game_data/<string:lobby_id>", methods=['POST'])
def get_game_data(lobby_id):
    the_lobby = lobby_manager.get_lobby(lobby_id)
    if the_lobby is None:
        return {"error": f"The lobby with id {lobby_id} does not exist."}, 502
    the_game = the_lobby.game
    return the_game.game_data


@app.route("/rename_player", methods=['POST'])
def rename_player():
    lobby_id = request.json.get("lobby_id")
    user_id = request.json.get("user_id")
    new_user_name = request.json.get("new_user_name")
    if new_user_name == "":
        raise ValueError("User name can not be empty")
    if len(new_user_name) > 64:
        raise ValueError("User name is too long")
    session['user_name'] = new_user_name  # update the name
    # also update the name in the lobby (if the user is currently in one)
    if lobby_id is not None:
        lobby_manager.update_player_name_in_lobby(lobby_id, user_id, new_user_name)
    return {"status": f"Player name successfully changed to {new_user_name}"}


@app.route("/change_color", methods=['POST'])
def change_color():
    lobby_id = request.json.get("lobby_id")
    user_id = request.json.get("user_id")
    new_color = request.json.get("new_color")
    session['user_color'] = new_color  # update the color
    # also update the name in the lobby (if the user is currently in one)
    if lobby_id is not None:
        lobby_manager.update_color_of_player_in_lobby(lobby_id, user_id, new_color)
    return {
        "status": f"Color successfully updated",
        "color": new_color
    }


def log_in_user():
    if "user_id" in session:
        # user is already logged in
        the_user = user.User()
        the_user.id = session['user_id']
        the_user.name = session['user_name']
        the_user.color = session['user_color']
        return the_user
    else:
        # user not registered yet, create new
        new_user = user.User()
        session['user_id'] = new_user.id
        session['user_name'] = new_user.name
        session['user_color'] = new_user.color
        return new_user


if __name__ == '__main__':
    # app.run(host="0.0.0.0", port=80, debug=False)  # use me for prod
    app.run(host="127.0.0.1", port=5009, debug=False)
