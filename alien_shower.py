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
	world.append("")
	world.append(" " * width)
	world.append("_" * width)
	for i in range(sky_height):
		world.append("   " * width)
	world.append("." * width)
	world.append(" ".join(" w " for i in range(num_ships)))
	world.append(" ".join(f"({i})" for i in range(num_ships)))
	world.append("")
	world.append(f"time left: 0.0")
	world.append(f"life: {0}, shots: {0}")
	world.append("")
	world.append(feedback)

	return ships, enemy_appearance, world

def show_help(stdscr, num_missiles):
	stdscr.clear()
	while stdscr.getch() == -1:
		stdscr.addstr(0, 0, "Welcome to Alien Shower.")
		stdscr.addstr(1, 0, "Your task is to protect the earth from incoming aliens.")
		stdscr.addstr(2, 0, "You can activate any ship by pressing the respective number.")
		stdscr.addstr(3, 0, "You can steer left and right by pressing \"a\" or \"d\".")
		stdscr.addstr(4, 0, "You can shoot by pressing \"s\".")
		stdscr.addstr(5, 0, "Be warned, though:")
		stdscr.addstr(6, 0, "Any missed shot will result in destruction.")
		stdscr.addstr(7, 0, "Your ships can only move so far.")
		stdscr.addstr(8, 0, f"Your ships can only fire {num_missiles} times.")
		stdscr.addstr(9, 0, "You may only have one ship active at a time.")
		stdscr.addstr(10, 0, "So look at where the next enemy will come from and plan ahead - but don't take too much time.")
		stdscr.addstr(11, 0, "Have fun!")
		stdscr.addstr(12, 0, "(Press a key to resume, press another to start...)")
		stdscr.refresh()

def wait_for_start(stdscr, world):
	stdscr.clear()
	while stdscr.getch() == -1:
		for i, line in enumerate(world):
			stdscr.addstr(i, 0, line)
		stdscr.refresh()

def update_world(world, sky_height, active_ship, active_enemy, active_shots, ships, enemy_appearance, stats, countdown, feedback):
	num_ships = len(ships)
	world.clear()
	world.append(f"wins: {stats['wins']}, losses: {stats['losses']}")
	world.append("")
	world.append(" ".join(" m " if enemy_appearance and enemy_appearance[-1] == i else "   " for i in range(num_ships)))
	world.append("_" * len(world[-1]))
	for j in range(sky_height):
		world.append(" ".join(" * " if active_shots and any(pos["pos_x"] == i and pos["pos_y"] == j for pos in active_shots)
								else " m " if active_enemy and active_enemy["pos_x"] == i and active_enemy["pos_y"] == j
								else "   " for i in range(num_ships)))
	world.append(".".join(".w." if active_ship and active_ship["pos"] == i else "..." for i in range(num_ships)))
	world.append(" ".join(" w " if ships[i] == "inactive" else "   " for i in range(num_ships)))
	world.append(" ".join(f"({i})" for i in range(num_ships)))
	world.append("")
	world.append(f"time left: {countdown:.1f}")
	world.append(f"life: {0 if not active_ship else active_ship['lifetime']}, shots: {0 if not active_ship else active_ship['shots']}")
	world.append("")
	world.append(feedback)

def update_state(active_ship, active_enemy, active_shots, ships, enemy_appearance, sky_height, stats):
	feedback = " " * 20
	# check ship lifetime
	if active_ship and (active_ship["lifetime"] <= 0 or active_ship["shots"] <= 0):
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
			feedback = "alien destroyed     "
			continue
		# handle world-border reached
		elif active_shots[i]["pos_y"] < 0:
			stats["losses"] += 1
			return True, "missed shot          \ndestroyed by aliens "
		else:
			active_shots[i]["pos_y"] -= 1
		i += 1
	# move enemy
	if active_enemy:
		active_enemy["pos_y"] += 1
		if active_enemy["pos_y"] >= sky_height:
			stats["losses"] += 1
			return True, feedback + "\ndestroyed by aliens "
	else:
		# set new enemy if in store
		if enemy_appearance:
			active_enemy["pos_x"] = enemy_appearance.pop()
			active_enemy["pos_y"] = 0
		else:
			stats["wins"] += 1
			return True, feedback + "\nall aliens destroyed"
	return False, feedback + "\n" + " " * 20

def process_input(key, active_ship, active_shots, ships, sky_height, num_missiles):
	num_ships = len(ships)
	if key == 27:
		return False
	# activate ship
	if not active_ship and key >= 48 and key < 58:
		value = key - 48
		if value < num_ships and ships[value] == "inactive":
			ships[value] = "active"
			active_ship["pos"] = value
			active_ship["lifetime"] = (num_ships*num_missiles)//2
			active_ship["base"] = value
			active_ship["shots"] = num_missiles
	else:
		# move ship to the left
		if key == 97 and active_ship["pos"] > 0: #a
			active_ship["pos"] -= 1
			active_ship["lifetime"] -=1
		# move ship to the right
		if key == 100 and active_ship["pos"] < num_ships-1: #d
			active_ship["pos"] += 1
			active_ship["lifetime"] -=1
		# fire
		if key == 115: #s
			active_shots.append({"pos_x": active_ship["pos"], "pos_y": sky_height})
			active_ship["shots"] -= 1
	return True

def game(stdscr, num_ships, sky_height, num_missiles, timeleft, no_help):
	# init game state
	stats = {"wins": 0, "losses": 0}
	ships, enemy_appearance, world = init_game(num_ships, sky_height, num_missiles)
	# don't wait for input (while showing a black input screen)
	stdscr.nodelay(True)
	# hide cursor
	curses.curs_set(0)
	# show help and initial world and wait for user input (any key) to start
	if not no_help:
		show_help(stdscr, num_missiles)
	wait_for_start(stdscr, world)
	# game loop
	stdscr.clear()
	in_game = True
	new_game = False
	feedback = " " * 20 + "\n" + " " * 20
	active_ship = {}
	active_enemy = {}
	active_shots = []
	clock = time.clock()
	delta_t = 0
	while in_game:
		# time it
		if delta_t < timeleft:
			delta_t = time.clock() - clock
		else:
			clock = time.clock()
			delta_t = time.clock() - clock
			# process input
			in_game = process_input(stdscr.getch(), active_ship, active_shots, ships, sky_height, num_missiles)
			# update state
			new_game, feedback = update_state(active_ship, active_enemy, active_shots, ships, enemy_appearance, sky_height, stats)
		# update the world
		update_world(world, sky_height, active_ship, active_enemy, active_shots, ships, enemy_appearance, stats, timeleft - delta_t, feedback)
		# draw the world
		for i, line in enumerate(world):
			stdscr.addstr(i, 0, line)
		stdscr.refresh()
		# check for new game
		if new_game:
			ships, enemy_appearance, world = init_game(num_ships, sky_height, num_missiles, stats["wins"], stats["losses"], feedback)
			new_game = False
			active_ship = {}
			active_enemy = {}
			active_shots = []
			wait_for_start(stdscr, world)
			clock = time.clock()
			delta_t = 0
	# show goodbye screen
	stdscr.clear()
	while stdscr.getch() == -1:
		stdscr.addstr(0, 0, "Thanks for playing Alien Shower.")
		stdscr.addstr(1, 0, "Your final score:")
		stdscr.addstr(2, 0, f"{stats['wins']} wins to {stats['losses']} losses.")
		stdscr.addstr(3, 0, "Bye!")
		stdscr.addstr(4, 0, "(Press a key to quit)")
		stdscr.refresh()

def run(num_ships=5, sky_height=4, num_missiles=2, speed=1, no_help=False):
	curses.wrapper(game, num_ships, sky_height, num_missiles, speed, no_help)

def main():
	parser = argparse.ArgumentParser(description="A kind of round-based space invader tetris mix.")
	parser.add_argument("--ships", type=int, default=5, help="the number of ships")
	parser.add_argument("--sky", type=int, default=4, help="the sky height")
	parser.add_argument("--missiles", type=int, default=2, help="the number of missiles of each ship")
	parser.add_argument("--speed", type=int, default=1, help="the countdown for movement decisions and the amount of time enemies and bullets require to move")
	parser.add_argument("--no_help", action="store_true", help="deactivate help")
	args = parser.parse_args()
	run(args.ships, args.sky, args.missiles, args.speed, args.no_help)

if __name__ == "__main__":
	main()
