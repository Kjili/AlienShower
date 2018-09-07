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

def addstr_format(stdscr, x, y, string, *positions, form=[curses.A_BOLD], split_at=" "):
	if not positions:
		return
	if len(form) < 2:
		form.append(curses.A_NORMAL)
	string_array = string.split(split_at)
	stdscr.addstr(x, y, "")
	last_pos = 0
	for pos in positions:
		if last_pos != pos:
			stdscr.addstr(split_at.join(string_array[last_pos:pos]) + split_at, form[1])
		else:
			stdscr.addstr(split_at.join(string_array[last_pos:pos]), form[1])
		stdscr.addstr(f"{string_array[pos]}", form[0])
		stdscr.addstr(split_at, form[1])
		last_pos = pos + 1
	stdscr.addstr(split_at.join(string_array[last_pos:]), form[1])

def show_help(stdscr, num_missiles, num_ships):
	stdscr.clear()
	while stdscr.getch() == -1:
		addstr_format(stdscr, 0, 0, "Welcome to Alien Shower.", 2, 3)
		stdscr.addstr(2, 0, "Your task is to protect the earth from invading aliens.")
		stdscr.addstr(3, 0, "To fulfill this task you have a fleet of ships at your disposal.")
		stdscr.addstr(4, 0, "You will need all of them to succeed.")
		stdscr.addstr(6, 0, "(Press any key to resume...)", curses.A_ITALIC)
	stdscr.clear()
	while stdscr.getch() == -1:
		stdscr.addstr(0, 0, "Controls:", curses.A_UNDERLINE)
		addstr_format(stdscr, 2, 0, "You can activate any ship by pressing the respective number.", 2, 4, 9)
		addstr_format(stdscr, 3, 0, "You can steer left and right by pressing \"a\" or \"d\".", 2, 8, 10)
		addstr_format(stdscr, 4, 0, "You can shoot by pressing \"s\".", 2, 5)
		addstr_format(stdscr, 5, 0, "You can increase/decrease the speed by pressing \"+\"/\"-\".", 4, 7)
		addstr_format(stdscr, 6, 0, "You can end the game and view your score by pressing \"escape\".", 2, 11)
		addstr_format(stdscr, 7, 0, "After each round, you can start a new one by pressing \"return\".", 5, 11)
		stdscr.addstr(9, 0, "(Press any key to resume...)", curses.A_ITALIC)
	stdscr.clear()
	while stdscr.getch() == -1:
		stdscr.addstr(0, 0, "Warning:", curses.A_UNDERLINE)
		addstr_format(stdscr, 2, 0, f"Each ship can only move {(num_ships*num_missiles)//2} times.", 4, 5, 6)
		addstr_format(stdscr, 3, 0, f"Each ship can only fire {num_missiles} times.", 4, 5, 6)
		addstr_format(stdscr, 4, 0, "You may only have one ship active at a time.", 4, 5, 6)
		addstr_format(stdscr, 5, 0, "You cannot deactivate a ship. Once one is wracked you may activate a new one.", 1, 2, 11, 12, 13)
		addstr_format(stdscr, 6, 0, "You have a small time frame to decide on an action, before an alien moves again.", 4, 5)
		stdscr.addstr(8, 0, "(Press any key to resume...)", curses.A_ITALIC)
	stdscr.clear()
	while stdscr.getch() == -1:
		stdscr.addstr(0, 0, "You will win, if:", curses.A_UNDERLINE)
		addstr_format(stdscr, 2, 0, "You destroy all aliens.", 1, 2)
		stdscr.addstr(4, 0, "You will loose, if:", curses.A_UNDERLINE)
		addstr_format(stdscr, 6, 0, "You miss a shot.", 1)
		addstr_format(stdscr, 7, 0, "A ship's lifetime expires before it makes it's last shot.", 2, 3)
		addstr_format(stdscr, 8, 0, "The aliens hit the ground.", 1, 2)
		stdscr.addstr(10, 0, "(Press any key to resume...)", curses.A_ITALIC)
	stdscr.clear()
	while stdscr.getch() != 10:
		stdscr.addstr(0, 0, "Remember:", curses.A_UNDERLINE)
		addstr_format(stdscr, 2, 0, f"Activate: {' '.join(list(map(lambda x: str(x % 10), range(1, num_ships + 1))))}", 0)
		addstr_format(stdscr, 3, 0, "Move: a d", 0)
		addstr_format(stdscr, 4, 0, "Shoot: s", 0)
		addstr_format(stdscr, 6, 0, "Change Speed: + -", 0, 1)
		stdscr.addstr(8, 0, "Look ahead to where the next enemy will come from and plan your move.")
		stdscr.addstr(9, 0, "But don't take too much time to act.")
		stdscr.addstr(10, 0, "Have fun!")
		stdscr.addstr(12, 0, "(Press return to resume to a gameboard overview, press return again to start...)", curses.A_ITALIC)

def game_snapshot(num_ships, sky_height, num_missiles, ships):
	# copy the ships to leave them unchanged for the game
	ships = ships.copy()
	# initialize a world
	world = []

	# add an enemy and enemy look-ahead
	active_enemy = {}
	active_enemy["pos_x"] = num_ships - 1
	active_enemy["pos_y"] = sky_height//3
	enemy_appearance = [max(0, num_ships//2 - 1)]

	# add a shot at the enemy if the sky_height is sufficiently large
	active_shots = []
	if sky_height > 1:
		active_shots.append({"pos_x": active_enemy["pos_x"], "pos_y": (2*sky_height)//3})

	# add a ship
	active_ship = {}
	feedback = " " * 20
	lifetime = (num_ships*num_missiles)//2 # same as ingame
	stats = {"wins": 0, "losses": 0, "destroyed": 0}
	# fixed look for low sky height
	if sky_height <= 1:
		start_at = active_enemy["pos_x"]
		active_ship["lifetime"] = 1
		active_ship["pos"] = active_enemy["pos_x"]
		active_ship["shots"] = 1
		feedback = "ship activated      "
	else:
		# no ship for one missile only (because it just shot...) and start at enemy position (for simplicity)
		if num_missiles <= 1:
			start_at = active_enemy["pos_x"]
			active_ship["lifetime"] = 0
		else:
			# arbitrary base position close to the enemy but not below
			temp_base = num_ships - 2
			# move the base if the lifetime is sufficient, otherwise leave it below the shot enemy
			if lifetime > active_enemy["pos_x"] - temp_base + active_enemy["pos_x"] - enemy_appearance[-1]:
				start_at = temp_base
			else:
				start_at = active_enemy["pos_x"]
			# move the ship position to the left if allowed by the shot position
			active_ship["pos"] = max(1, num_ships - min(3, sky_height - active_shots[0]["pos_y"]))
			# adapt the lifetime to the movement between base, enemy and current position
			active_ship["lifetime"] = lifetime - (active_enemy["pos_x"] - start_at + active_enemy["pos_x"] - active_ship["pos"])
			# count down the missiles
			active_ship["shots"] = num_missiles - 1
	ships[start_at] = "active"
	active_ship["base"] = start_at
	# if only one missile is available, there is no active ship
	# set the shot position to minimum to be able to show the ship wracked message for better feedback
	if active_ship["lifetime"] == 0:
		active_ship = {}
		active_shots[0]["pos_y"] = sky_height - 1
		feedback = ("ship wracked        ")

	# if enough ships exist, display one as wracked
	if num_ships > 3:
		stats["destroyed"] = num_missiles
		ships[max(0, num_ships//2 - 1)] = "wracked"
	# if even more ships exist, display two as wracked
	if num_ships > 6:
		stats["destroyed"] = num_missiles*2
		ships[1] = "wracked"
		ships[max(0, num_ships//2 - 1)] = "wracked"

	# set a countdown smaller than max countdown
	countdown = 2
	# set a feedback and how to continue
	feedback = feedback + "\n" + "hit return to start "

	# set activate ship action if none is active (choose a ship close to the next enemy)
	if not active_ship:
		start_ship_at = enemy_appearance[-1]
		i = 1
		while ships[start_ship_at] != "inactive":
			start_ship_at = (enemy_appearance[-1] - i) % 9
			i -= 1
		next_action = f"start ship {start_ship_at + 1}  "
	# set move action for active ship unless there is a reason to shoot
	elif sky_height > 1 and (active_ship["pos"] != active_enemy["pos_x"] or active_ship["pos"] == active_shots[0]["pos_x"]):
		next_action = "move left     "
	else:
		next_action = "shoot         "

	# create the world
	update_world(world, sky_height, active_ship, active_enemy, active_shots, ships, enemy_appearance, stats, countdown, feedback, next_action)
	return world

def init_game(num_ships, sky_height, num_missiles, wins=0, losses=0, feedback="hit return to start " + "\n" + " " * 20):
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
	world.append((f"wins: {wins}, losses: {losses}",))
	world.append(("aliens destroyed: 0  ",))
	world.append(("",))
	world.append((" " * width,))
	world.append(("_" * width,))
	for i in range(sky_height):
		world.append(("   " * width,))
	world.append(("." * width,))
	world.append((" ".join(" w " for i in range(num_ships)),))
	world.append((" ".join(f"({i})" for i in range(1, min(10, num_ships + 1))) + (" (0)" if num_ships == 10 else ""),))
	world.append(("",))
	world.append((f"time left: {chr(0x25a0) * (5 - 1)}",))
	world.append((f"next: no action     ", [1, 2]))
	world.append(("life: 0, shots: 0", [1, 3]))
	world.append(("",))
	world.append((feedback,))

	return ships, enemy_appearance, world

def update_world(world, sky_height, active_ship, active_enemy, active_shots, ships, enemy_appearance, stats, countdown, feedback, next_action):
	num_ships = len(ships)
	world.clear()
	world.append((f"wins: {stats['wins']}, losses: {stats['losses']}",))
	world.append((f"aliens destroyed: {stats['destroyed']}",))
	world.append(("",))
	world.append((" ".join(" m " if enemy_appearance and enemy_appearance[-1] == i else "   " for i in range(num_ships)),))
	world.append(("_" * len(world[-1][0]),))
	for j in range(sky_height):
		world.append((" ".join(" * " if active_shots and any(pos["pos_x"] == i and pos["pos_y"] == j for pos in active_shots)
								else " m " if active_enemy and active_enemy["pos_x"] == i and active_enemy["pos_y"] == j
								else "   " for i in range(num_ships)),))
	fleet = " ".join(" w " if ships[i] == "inactive" else "   " for i in range(num_ships))
	if active_ship:
		world.append((".".join(".w." if active_ship["pos"] == i else "..." for i in range(num_ships)), [active_ship["pos"]*4+1], [curses.A_BOLD], "."))
		world.append((fleet, range(len(fleet.split(" "))), [curses.A_DIM]))
		world.append((" ".join(f"({i})" for i in range(1, min(10, num_ships + 1))) + (" (0)" if num_ships == 10 else ""), range(num_ships), [curses.A_DIM]))
	else:
		world.append(("." * len(world[-1][0]),))
		world.append((fleet, range(len(fleet.split(" ")))))
		inactive_ships = [i for i in range(num_ships) if ships[i] != "inactive"]
		if inactive_ships:
			world.append((" ".join(f"({i})" for i in range(1, min(10, num_ships + 1))) + (" (0)" if num_ships == 10 else ""), inactive_ships, [curses.A_DIM, curses.A_BOLD]))
		else:
			world.append((" ".join(f"({i})" for i in range(1, min(10, num_ships + 1))) + (" (0)" if num_ships == 10 else ""),))
	world.append(("",))
	world.append((f"time left: {chr(0x25a0) * (countdown - 1)}    ",))
	world.append((f"next: {next_action}", [1, 2, 3]))
	world.append((f"life: {0 if not active_ship else active_ship['lifetime']}, shots: {0 if not active_ship else active_ship['shots']}    ", [1, 3]))
	world.append(("",))
	world.append((feedback,))

def draw_world(stdscr, world, color=0):
	world_len = len(world)
	for i, tpl in enumerate(world):
		# mark feedback lines bold (and colored if color is > 0)
		if i in (world_len - 1,):
			stdscr.addstr(i, 0, tpl[0], curses.A_BOLD | curses.color_pair(color))
			continue
		# mark the rest as given by the other tuple elements
		if len(tpl) > 3:
			addstr_format(stdscr, i, 0, tpl[0], *tpl[1], form=tpl[2], split_at=tpl[3])
		elif len(tpl) > 2:
			addstr_format(stdscr, i, 0, tpl[0], *tpl[1], form=tpl[2])
		elif len(tpl) > 1:
			addstr_format(stdscr, i, 0, tpl[0], *tpl[1])
		else:
			stdscr.addstr(i, 0, tpl[0])
		# mark win or loss if color is given
		if i == 0 and color == 1:
			addstr_format(stdscr, i, 0, tpl[0], 2, 3)
		if i == 0 and color == 2:
			addstr_format(stdscr, i, 0, tpl[0], 0, 1)

def update_state(active_ship, active_enemy, active_shots, ships, enemy_appearance, sky_height, num_missiles, stats, next_action, final_stats, feedback):
	### process input ###

	num_ships = len(ships)
	# activate the ship
	if not next_action:
		if not active_ship:
			feedback = "no ship activate yet" + "\n" + " " * 20
		else:
			feedback = "ship awaits commands" + "\n" + " " * 20
	# activate the ship
	elif next_action[0] == "activate":
		value = next_action[1]
		ships[value] = "active"
		active_ship["pos"] = value if value >= 0 else num_ships - 1
		active_ship["lifetime"] = (num_ships*num_missiles)//2
		active_ship["base"] = value if value >= 0 else num_ships - 1
		active_ship["shots"] = num_missiles
		feedback = "ship activated      " + "\n" + " " * 20
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
			final_stats["missed defence"][1] += 1
			return True, "ship life expired   \nhit return to retry "
		# based on shots
		if active_ship["shots"] <= 0:
			ships[active_ship["base"]] = "wracked"
			active_ship.clear()
			feedback = "ship wracked        " + "\n" + " " * 20
	# move shots
	i = 0
	while i < len(active_shots):
		# handle hit
		if active_enemy and (active_shots[i]["pos_x"] == active_enemy["pos_x"] and active_shots[i]["pos_y"] == active_enemy["pos_y"]
		or active_shots[i]["pos_x"] == active_enemy["pos_x"] and active_shots[i]["pos_y"]-1 == active_enemy["pos_y"]):
			active_enemy.clear()
			del active_shots[i]
			stats["destroyed"] += 1
			feedback = "alien destroyed     " + "\n" + " " * 20
			final_stats["aliens destroyed"][0] += 1
			continue
		# handle world-border reached, loose the game
		elif active_shots[i]["pos_y"] < 0:
			stats["losses"] += 1
			final_stats["missed shots"][0] += 1
			final_stats["missed defence"][1] += 1
			return True, "missed shot          \nhit return to retry "
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
			final_stats["missed defence"][1] += 1
			return True, "missing defence      \nhit return to retry "
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
			return True, "all aliens destroyed\nhit return for more "
	return False, feedback

def process_input(key, active_ship, ships, next_action, timeleft, feedback):
	# leave on escape
	if key == 27:
		return False, next_action, timeleft, feedback
	if key == 43: #+
		feedback = "speed increased     " + "\n" + " " * 20
		return True, next_action, timeleft - 0.1, feedback
	if key == 45: #-
		feedback = "speed decreased     " + "\n" + " " * 20
		return True, next_action, timeleft + 0.1, feedback
	# gather next action from input
	if not next_action:
		num_ships = len(ships)
		# activate ship
		if not active_ship and key >= 48 and key < 58:
			value = key - 49
			if value < num_ships:
				if ships[value] == "inactive":
					next_action = ("activate", value, f"start ship {value + 1}  ")
					feedback = " " * 20 + "\n" + " " * 20
				else:
					feedback = f"ship {value + 1} already active   " + "\n" + " " * 20
			else:
				feedback = f"no ship at position {value + 1}   " + "\n" + " " * 20
		if active_ship:
			# move ship to the left
			if key == 97 and active_ship["pos"] > 0: #a
				next_action = ("move", "left", "move left     ")
				feedback = " " * 20 + "\n" + " " * 20
			# move ship to the right
			if key == 100 and active_ship["pos"] < num_ships-1: #d
				next_action = ("move", "right", "move right    ")
				feedback = " " * 20 + "\n" + " " * 20
			# fire
			if key == 115 and active_ship["shots"] > 0: #s
				next_action = ("shoot", "", "shoot         ")
				feedback = " " * 20 + "\n" + " " * 20
			# give feedback for active ship
			if key >= 48 and key < 58:
				feedback = "ship already active     " + "\n" + " " * 20
	return True, next_action, timeleft, feedback

def wait_for_start(stdscr, world, color=0):
	stdscr.clear()
	while True:
		key = stdscr.getch()
		if key == 27:
			return True
		draw_world(stdscr, world, color)
		if key == 10:
			break
	return False

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
	sky_height = max(sky_height, num_ships-1, num_missiles) # adjust sky height to minimum to be able to win
	ships, enemy_appearance, world = init_game(num_ships, sky_height, num_missiles)
	# don't wait for input (while showing a black input screen)
	stdscr.nodelay(True)
	# hide cursor
	curses.curs_set(0)
	# use colors as used per default in the terminal
	curses.use_default_colors()
	curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
	curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
	# show help and initial world and wait for user input (any key) to start
	if not no_help:
		show_help(stdscr, num_missiles, num_ships)
	wait_for_start(stdscr, game_snapshot(num_ships, sky_height, num_missiles, ships))
	stdscr.clear()
	draw_world(stdscr, world)
	stdscr.refresh()
	time.sleep(1)
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
		in_game, next_action, timeleft, feedback = process_input(stdscr.getch(), active_ship, ships, next_action, timeleft, feedback)
		# update game state on next step
		if delta_t >= timeleft:
			# update state
			new_game, feedback = update_state(active_ship, active_enemy, active_shots, ships, enemy_appearance, sky_height, num_missiles, stats, next_action, final_stats, feedback)
			# clear action
			next_action = ()
			# renew clock
			clock = time.perf_counter()
		# time next step
		delta_t = time.perf_counter() - clock
		# update the world
		update_world(world, sky_height, active_ship, active_enemy, active_shots, ships, enemy_appearance, stats, 5-int(delta_t/(timeleft/5)), feedback, next_action[2] if next_action else "no action     ")
		# draw the world
		draw_world(stdscr, world)
		stdscr.refresh()
		# check for new game
		if new_game:
			new_game = False
			active_ship = {}
			active_enemy = {}
			active_shots = []
			if wait_for_start(stdscr, world, 2 if "all aliens destroyed" in feedback else 1):
				break
			ships, enemy_appearance, world = init_game(num_ships, sky_height, num_missiles, stats["wins"], stats["losses"], feedback)
			# draw the initial world
			draw_world(stdscr, world)
			stdscr.refresh()
			stats["destroyed"] = 0
			clock = time.perf_counter()
			delta_t = 0
	# show goodbye screen
	stdscr.clear()
	while stdscr.getch() == -1:
		stdscr.addstr(0, 0, "Thanks for playing Alien Shower.")
		stdscr.addstr(2, 0, "Your final score:")
		stdscr.addstr(4, 0, "Triumphs:")
		stdscr.addstr(4, 32, f"{stats['wins']}")
		stdscr.addstr(5, 0, "Losses:")
		stdscr.addstr(5, 32, f"{stats['losses']}")
		row = 6
		for key in final_stats:
			row += 1
			stdscr.addstr(row, 0, f"Total {key}:")
			stdscr.addstr(row, 32, f"{final_stats[key][0]} of {final_stats[key][1]}")
		stdscr.addstr(row + 2, 0, "(Press any key to quit)", curses.A_ITALIC)
		stdscr.refresh()

def run(difficulty="custom", num_ships=5, sky_height=4, num_missiles=2, speed=1, no_help=False):
	if num_ships < 2 or num_ships > 10:
		raise argparse.ArgumentTypeError(f"argument --ships: invalid choice: {num_ships} (choose from 2, 3, 4, 5, 6, 7, 8, 9, 10)")
	if num_missiles < 1:
		raise argparse.ArgumentTypeError(f"argument --missiles: invalid choice: {num_missiles} (must be larger than 0)")
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
