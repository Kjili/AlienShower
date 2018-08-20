##
 # A kind of round-based space invader tetris mix.
 #
 # Copyright (C) 2018  Annemarie Mattmann
 #
 # This program is free software: you can redistribute it and/or modify
 # it under the terms of the GNU General Public License as published by
 # the Free Software Foundation, either version 3 of the License, or
 # (at your option) any later version.
 #
 # This program is distributed in the hope that it will be useful,
 # but WITHOUT ANY WARRANTY; without even the implied warranty of
 # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 # GNU General Public License for more details.
 #
 # You should have received a copy of the GNU General Public License
 # along with this program.  If not, see <https://www.gnu.org/licenses/>.
##

import curses
import time
import random
import argparse

def init_game(num_ships, sky_height, num_missiles, wins=0, losses=0, feedback=" " * 20 + "\n" + " " * 20):
	# init ships
	ships = []
	for i in range(num_ships):
		ships.append("inactive")

	# init enemies (as positions they will appear at)
	enemy_appearance = list(range(num_ships)) * num_missiles
	random.shuffle(enemy_appearance)

	# init world
	world = []
	width = num_ships*3 + num_ships - 1
	world.append(f"wins: {wins}, losses: {losses}")
	world.append("aliens destroyed: 0  ")
	world.append("")
	world.append(" " * width)
	world.append("_" * width)
	for i in range(sky_height):
		world.append("   " * width)
	world.append("." * width)
	world.append(" ".join(" w " for i in range(num_ships)))
	world.append(" ".join(f"({i})" for i in range(1, min(10, num_ships + 1))) + (" (0)" if num_ships == 10 else ""))
	world.append("")
	world.append("time left: 0.0")
	world.append(f"next: no action     ")
	world.append("life: 0, shots: 0")
	world.append("")
	world.append(feedback)

	return ships, enemy_appearance, world

def addstr_format(stdscr, x, y, string, *positions, form=curses.A_BOLD):
	if not positions:
		return
	string_array = string.split(" ")
	stdscr.addstr(x, y, "")
	last_pos = 0
	for pos in positions:
		stdscr.addstr(" ".join(string_array[last_pos:pos]))
		stdscr.addstr(f" {string_array[pos]} " if last_pos != pos else f"{string_array[pos]} ", form)
		last_pos = pos + 1
	stdscr.addstr(" ".join(string_array[last_pos:]))

def show_help(stdscr, num_missiles, num_ships):
	stdscr.clear()
	while stdscr.getch() == -1:
		addstr_format(stdscr, 0, 0, "Welcome to Alien Shower.", 2, 3)
		stdscr.addstr(1, 0, "Your task is to protect the earth from incoming aliens.")
		addstr_format(stdscr, 2, 0, "You can activate any ship by pressing the respective number.", 2, 4, 9)
		addstr_format(stdscr, 3, 0, "You can steer left and right by pressing \"a\" or \"d\".", 2, 8, 10)
		addstr_format(stdscr, 4, 0, "You can shoot by pressing \"s\".", 2, 5)
		stdscr.addstr(5, 0, "Be warned, though:")
		stdscr.addstr(6, 0, "Any missed shot will result in destruction.")
		addstr_format(stdscr, 7, 0, f"Each ship can only move {(num_ships*num_missiles)//2} times.", 4, 5, 6)
		addstr_format(stdscr, 8, 0, f"Each ship can only fire {num_missiles} times.", 4, 5, 6)
		addstr_format(stdscr, 9, 0, "You may only have one ship active at a time.", 4, 5, 6)
		addstr_format(stdscr, 10, 0, "Once it is wracked you may activate a new one. You cannot deactivate a ship.", 6, 7, 8, 11, 12)
		stdscr.addstr(11, 0, "So look ahead to where the next enemy will come from and plan your move.")
		addstr_format(stdscr, 12, 0, "But don't take too much time to act.", 5)
		stdscr.addstr(13, 0, "Have fun!")
		stdscr.addstr(14, 0, "(Press escape to end the game and view your score.)")
		stdscr.addstr(15, 0, "(Press return to resume now, press return again to start...)")

def wait_for_start(stdscr, world):
	stdscr.clear()
	while True:
		key = stdscr.getch()
		if key == 27:
			return True
		for i, line in enumerate(world):
			stdscr.addstr(i, 0, line)
		if key == 10:
			break
	return False

def update_world(world, sky_height, active_ship, active_enemy, active_shots, ships, enemy_appearance, stats, countdown, feedback, next_action):
	num_ships = len(ships)
	world.clear()
	world.append(f"wins: {stats['wins']}, losses: {stats['losses']}")
	world.append(f"aliens destroyed: {stats['destroyed']}")
	world.append("")
	world.append(" ".join(" m " if enemy_appearance and enemy_appearance[-1] == i else "   " for i in range(num_ships)))
	world.append("_" * len(world[-1]))
	for j in range(sky_height):
		world.append(" ".join(" * " if active_shots and any(pos["pos_x"] == i and pos["pos_y"] == j for pos in active_shots)
								else " m " if active_enemy and active_enemy["pos_x"] == i and active_enemy["pos_y"] == j
								else "   " for i in range(num_ships)))
	world.append(".".join(".w." if active_ship and active_ship["pos"] == i else "..." for i in range(num_ships)))
	world.append(" ".join(" w " if ships[i] == "inactive" else "   " for i in range(num_ships)))
	world.append(" ".join(f"({i})" for i in range(1, min(10, num_ships + 1))) + (" (0)" if num_ships == 10 else ""))
	world.append("")
	world.append(f"time left: {countdown:.1f}")
	world.append(f"next: {next_action}")
	world.append(f"life: {0 if not active_ship else active_ship['lifetime']}, shots: {0 if not active_ship else active_ship['shots']}    ")
	world.append("")
	world.append(feedback)

def update_state(active_ship, active_enemy, active_shots, ships, enemy_appearance, sky_height, num_missiles, stats, next_action, final_stats):
	feedback = " " * 20

	### process input ###

	num_ships = len(ships)
	# activate the ship
	if not next_action:
		feedback = "no action specified "
	# activate the ship
	elif next_action[0] == "activate":
		value = next_action[1]
		ships[value] = "active"
		active_ship["pos"] = value if value >= 0 else num_ships - 1
		active_ship["lifetime"] = (num_ships*num_missiles)//2
		active_ship["base"] = value if value >= 0 else num_ships - 1
		active_ship["shots"] = num_missiles
		feedback = "ship activated      "
		final_stats["ships lifetime expired"][1] += 1
		final_stats["moves made"][1] += active_ship["lifetime"]
	# move the ship
	elif next_action[0] == "move":
		if next_action[1] == "left":
			active_ship["pos"] -= 1
			active_ship["lifetime"] -=1
		if next_action[1] == "right":
			active_ship["pos"] += 1
			active_ship["lifetime"] -=1
		final_stats["moves made"][0] += 1
	# fire
	elif next_action[0] == "shoot":
		active_shots.append({"pos_x": active_ship["pos"], "pos_y": sky_height})
		active_ship["shots"] -= 1
		final_stats["missed shots"][1] += 1

	### update game state ###

	# check ship lifetime
	if active_ship:
		# based on movement and if a shot remains, loose the game
		if active_ship["lifetime"] <= 0 and active_ship["shots"] > 0:
			ships[active_ship["base"]] = "wracked"
			active_ship.clear()
			stats["losses"] += 1
			final_stats["ships lifetime expired"][0] += 1
			return True, "ship life expired   \ndestroyed by aliens "
		# based on shots
		if active_ship["shots"] <= 0:
			ships[active_ship["base"]] = "wracked"
			active_ship.clear()
			feedback = "ship wracked        "
	# move shots
	i = 0
	while i < len(active_shots):
		# handle hit
		if active_enemy and (active_shots[i]["pos_x"] == active_enemy["pos_x"] and active_shots[i]["pos_y"] == active_enemy["pos_y"]
		or active_shots[i]["pos_x"] == active_enemy["pos_x"] and active_shots[i]["pos_y"]-1 == active_enemy["pos_y"]):
			active_enemy.clear()
			del active_shots[i]
			stats["destroyed"] += 1
			feedback = "alien destroyed     "
			final_stats["aliens destroyed"][0] += 1
			continue
		# handle world-border reached, loose the game
		elif active_shots[i]["pos_y"] < 0:
			stats["losses"] += 1
			final_stats["missed shots"][0] += 1
			return True, "missed shot          \ndestroyed by aliens "
		# handle move
		else:
			active_shots[i]["pos_y"] -= 1
		i += 1
	# move enemy
	if active_enemy:
		active_enemy["pos_y"] += 1
		# loose the game
		if active_enemy["pos_y"] >= sky_height:
			stats["losses"] += 1
			final_stats["missed defence"][0] += 1
			return True, "missing defence      \ndestroyed by aliens "
	else:
		# set new enemy if in store
		if enemy_appearance:
			active_enemy["pos_x"] = enemy_appearance.pop()
			active_enemy["pos_y"] = 0
			final_stats["aliens destroyed"][1] += 1
		# win the game
		else:
			stats["wins"] += 1
			final_stats["missed defence"][1] += 1
			return True, feedback + "\nall aliens destroyed"
	return False, feedback + "\n" + " " * 20

def process_input(key, active_ship, ships, next_action):
	# leave on escape
	if key == 27:
		return False, next_action
	# gather next action from input
	num_ships = len(ships)
	# activate ship
	if not active_ship and key >= 48 and key < 58:
		value = key - 49
		if value < num_ships and ships[value] == "inactive":
			next_action = ("activate", value, f"start ship {value + 1}  ")
	if active_ship:
		# move ship to the left
		if key == 97 and active_ship["pos"] > 0: #a
			next_action = ("move", "left", "move left     ")
		# move ship to the right
		if key == 100 and active_ship["pos"] < num_ships-1: #d
			next_action = ("move", "right", "move right    ")
		# fire
		if key == 115 and active_ship["shots"] > 0: #s
			next_action = ("shoot", "", "shoot         ")
	return True, next_action

def game(stdscr, num_ships, sky_height, num_missiles, timeleft, no_help):
	# check for sky height plus game stats not exceeding terminal height
	# as curses crashes with an error if the cursor moves out of the screen
	scr_height, _ = stdscr.getmaxyx()
	if scr_height < sky_height + 15:
		raise argparse.ArgumentTypeError(f"argument --sky: invalid size: {sky_height} (must fit into your terminal, either resize it's height or reduce the sky_height to a maximum of {scr_height - 15})")
	# init game state
	stats = {"wins": 0, "losses": 0, "destroyed": 0}
	final_stats = {
		"aliens destroyed": [0, 0],
		"moves made": [0, 0],
		"missed defence": [0, 0],
		"missed shots": [0, 0],
		"ships lifetime expired": [0, 0]
	}
	sky_height = max(sky_height, num_ships-1) # adjust sky height to minimum to be able to win
	ships, enemy_appearance, world = init_game(num_ships, sky_height, num_missiles)
	# don't wait for input (while showing a black input screen)
	stdscr.nodelay(True)
	# hide cursor
	curses.curs_set(0)
	# show help and initial world and wait for user input (any key) to start
	if not no_help:
		show_help(stdscr, num_missiles, num_ships)
	wait_for_start(stdscr, world)
	# game loop
	stdscr.clear()
	in_game = True
	new_game = False
	feedback = " " * 20 + "\n" + " " * 20
	active_ship = {}
	active_enemy = {}
	active_shots = []
	next_action = ()
	clock = time.perf_counter()
	delta_t = 0
	while in_game:
		# process input
		in_game, next_action = process_input(stdscr.getch(), active_ship, ships, next_action)
		# update game state on next step
		if delta_t >= timeleft:
			# update state
			new_game, feedback = update_state(active_ship, active_enemy, active_shots, ships, enemy_appearance, sky_height, num_missiles, stats, next_action, final_stats)
			# clear action
			next_action = ()
			# renew clock
			clock = time.perf_counter()
		# time next step
		delta_t = time.perf_counter() - clock
		# update the world
		update_world(world, sky_height, active_ship, active_enemy, active_shots, ships, enemy_appearance, stats, timeleft - delta_t, feedback, next_action[2] if next_action else "no action     ")
		# draw the world
		for i, line in enumerate(world):
			stdscr.addstr(i, 0, line)
		stdscr.refresh()
		# check for new game
		if new_game:
			new_game = False
			active_ship = {}
			active_enemy = {}
			active_shots = []
			if wait_for_start(stdscr, world):
				break
			ships, enemy_appearance, world = init_game(num_ships, sky_height, num_missiles, stats["wins"], stats["losses"], feedback)
			# draw the initial world
			for i, line in enumerate(world):
				stdscr.addstr(i, 0, line)
			stdscr.refresh()
			stats["destroyed"] = 0
			clock = time.perf_counter()
			delta_t = 0
	# show goodbye screen
	stdscr.clear()
	while stdscr.getch() == -1:
		stdscr.addstr(0, 0, "Thanks for playing Alien Shower.")
		stdscr.addstr(1, 0, "Your final score:")
		stdscr.addstr(2, 0, f"{stats['wins']} wins to {stats['losses']} losses.")
		stdscr.addstr(3, 0, "")
		row = 3
		for key in final_stats:
			row += 1
			stdscr.addstr(row, 0, f"Total {key}: {final_stats[key][0]} of {final_stats[key][1]}")
		stdscr.addstr(row + 1, 0, "")
		stdscr.addstr(row + 2, 0, "Bye!")
		stdscr.addstr(row + 3, 0, "(Press a key to quit)")
		stdscr.refresh()

def run(difficulty="custom", num_ships=5, sky_height=4, num_missiles=2, speed=1, no_help=False):
	if num_ships < 2 or num_ships > 10:
		raise argparse.ArgumentTypeError(f"argument --ships: invalid choice: {num_ships} (choose from 2, 3, 4, 5, 6, 7, 8, 9, 10)")
	if difficulty == "easy":
		num_ships=5
		sky_height=8
		num_missiles=2
		speed=1
	if difficulty == "normal":
		num_ships=5
		sky_height=4
		num_missiles=2
		speed=1
	if difficulty == "hard":
		num_ships=10
		sky_height=4 # will be overwritten
		num_missiles=2
		speed=0.5
	if difficulty == "brainfuck":
		num_ships=10
		sky_height=4 # will be overwritten
		num_missiles=3
		speed=0.3
	curses.wrapper(game, num_ships, sky_height, num_missiles, speed, no_help)

def main():
	parser = argparse.ArgumentParser(description="A kind of round-based space invader tetris mix.")
	parser.add_argument("--difficulty", choices=["easy", "normal", "hard", "brainfuck", "custom"], default="custom", metavar="", help="the difficulty which predefines the number of ships, sky height, missiles and speed and overwrites their values unless set to custom [easy: normal game with high sky, normal: normal game (challenging for beginners), hard: faster coundown and more ships, brainfuck: even faster countdown and more shots to make, custom: choose your own difficulty from super easy to inhuman by adjusting the parameters]")
	parser.add_argument("--ships", choices=[2, 3, 4, 5, 6, 7, 8, 9, 10], type=int, default=5, metavar="[2, ..., 10]", help="the number of ships (will be overwritten unless the difficulty is set to custom)")
	parser.add_argument("--sky", type=int, default=4, metavar="", help="the sky height (will be overwritten unless the difficulty is set to custom or if the game would be unplayable)")
	parser.add_argument("--missiles", type=int, default=2, metavar="", help="the number of missiles of each ship (will be overwritten unless the difficulty is set to custom)")
	parser.add_argument("--speed", type=float, default=1.0, metavar="", help="the countdown for movement decisions and the amount of time enemies and bullets require to move in seconds (will be overwritten unless the difficulty is set to custom)")
	parser.add_argument("--no_help", action="store_true", help="deactivate help")
	args = parser.parse_args()
	run(args.difficulty, args.ships, args.sky, args.missiles, args.speed, args.no_help)

if __name__ == "__main__":
	main()
