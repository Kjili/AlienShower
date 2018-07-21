import curses
import time
import random
import argparse

parser = argparse.ArgumentParser(description="A kind of space invader tetris mix.")
parser.add_argument("--ships", type=int, default=5, help="the number of ships")
parser.add_argument("--sky", type=int, default=4, help="the sky height")
parser.add_argument("--missiles", type=int, default=2, help="the number of missiles of each ship")
args = parser.parse_args()

# set params
num_ships = args.ships
sky_height = args.sky
num_missiles = args.missiles

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
world.append(" " * width)
world.append("_" * width)
for i in range(sky_height):
	world.append("   " * width)
world.append("." * width)
world.append(" ".join(" w " for i in range(num_ships)))
world.append(" ".join(f"({i})" for i in range(num_ships)))

def update_world(active_ship, active_enemy, active_shot):
	world.clear()
	world.append(" ".join(" m " if enemy_appearance and enemy_appearance[-1] == i else "   " for i in range(num_ships)))
	world.append("_" * width)
	for j in range(sky_height):
		world.append(" ".join(" * " if active_shot and any(pos["pos_x"] == i and pos["pos_y"] == j for pos in active_shot) else " m " if active_enemy and active_enemy["pos_x"] == i and active_enemy["pos_y"] == j else "   " for i in range(num_ships)))
	world.append(".".join(".w." if active_ship and active_ship["pos"] == i else "..." for i in range(num_ships)))
	world.append(" ".join(" w " if ships[i] == "inactive" else "   " for i in range(num_ships)))
	world.append(" ".join(f"({i})" for i in range(num_ships)))

def update_objects(active_enemy, active_shot):
	for shot in active_shot:
		if active_enemy and shot["pos_x"] == active_enemy["pos_x"] and shot["pos_y"] == active_enemy["pos_y"]:
			active_enemy = None
			shot["pos_y"] = -1
		if shot["pos_y"] >= 0:
			shot["pos_y"] -= 1
		if active_enemy and shot["pos_x"] == active_enemy["pos_x"] and shot["pos_y"] == active_enemy["pos_y"]:
			active_enemy = None
			shot["pos_y"] = -1
	if active_enemy:
		active_enemy["pos_y"] += 1
		if active_enemy["pos_y"] > sky_height:
			# loss
			pass
	if not active_enemy:
		if enemy_appearance:
			active_enemy = {"pos_x": enemy_appearance.pop(), "pos_y": 0}
		else:
			# win
			pass
	return active_enemy, active_shot

def process_input(key, active_ship, active_shot):
	if key.isdigit():
		value = int(key)
		if value < num_ships and not "active" in ships and ships[value] == "inactive":
			ships[value] = "active"
			active_ship = {"pos": value, "lifetime": (num_ships*num_missiles)/2, "base": value, "shots": num_missiles}
	if active_ship:
		if key == "a" and active_ship["pos"] > 0:
			active_ship["pos"] -= 1
			active_ship["lifetime"] -=1
		if key == "d" and active_ship["pos"] < num_ships-1:
			active_ship["pos"] += 1
			active_ship["lifetime"] -=1
		if key == "s":
			#shoot
			active_shot.append({"pos_x": active_ship["pos"], "pos_y": sky_height})
			active_ship["shots"] -= 1
		if active_ship["lifetime"] <= 0 or active_ship["shots"] <= 0:
			ships[active_ship["base"]] = "wracked"
			active_ship = None
	return active_ship, active_shot

def main(stdscr):
	stdscr.nodelay(True) # don't wait for input
	active_ship = None
	active_enemy = None
	active_shot = []
	while True:
		# draw the world
		stdscr.clear()
		for i, line in enumerate(world):
			stdscr.addstr(line + "\n")#i, 0, line)
		stdscr.refresh()
		# sleep
		time.sleep(1)
		try: # do not throw an exception if no key is given
			active_ship, active_shot = process_input(stdscr.getkey(), active_ship, active_shot)
		except:
			pass
		active_enemy, active_shot = update_objects(active_enemy, active_shot)
		# update the world
		update_world(active_ship, active_enemy, active_shot)

curses.wrapper(main)
