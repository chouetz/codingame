import sys
import math


def d(*x):
    print(*x, file=sys.stderr)


def a(xs, ys, r=1):
    return tuple(x + r * y for x, y in zip(xs, ys))


x_min, x_max = 0, 16000
y_min, y_max = 0, 9000
nx_max, ny_max = 6, 4
view = 2200
buster_move = 800
trap_min = 900
trap_max = 1760
release_limit = 1600
coins = [(x_min + release_limit, y_min + release_limit), (x_max - release_limit, y_min + release_limit),
         (x_min + release_limit, y_max - release_limit), (x_max - release_limit, y_max - release_limit)]
ghost_move = 400
GHOST = -1
actions = {0: 'move', 1: 'carry', 2: 'stun', 3: 'bust'}
global scan


def diag(x):
    return int(y_max - y_max * x / x_max)


def in_bounds(t):
    return 0 <= t[0] < nx_max and 0 <= t[1] < ny_max


def init_pos():
    s = sorted(busters, key=lambda b: b.x)
    # d(s)
    for i in range(len(s)):
        if s[i].type == GHOST:
            continue
        if s[i].i not in view_pos:
            if nbBusters == 1:
                delta = 0
            else:
                if i % nbBusters == 0:
                    delta = -1200
                elif i % nbBusters == nbBusters - 1:
                    delta = 1200
                else:
                    delta = 0
            x_buster = int(((i % nbBusters) + 1) * x_max / (nbBusters + 1) + delta)
            view_pos[s[i].i] = Entity(x=x_buster, y=diag(x_buster), state=16)


def la_carotte(carotte):
    global total, secure
    in_view = 0
    for b in busters:
        if b.type == hisTeam:
            if b.visible:
                in_view += 1
            if actions[b.state] != 'stun' and b.dist(base) < 3000 and total >= secure - 1:
                return True
    return False if in_view >= nbBusters - 1 and carotte is True else carotte


def treat_weaks():
    for b in busters:
        # fill in weaks
        if not weaks[b.i]:
            for g in ghosts:
                if g.dist(b) <= view and (g.state <= 3 or (g.state < weak_life and b.dist(base) > 6200)):
                    weaks[b.i] = True


def norm_life(life):
    if life < 9:
        return life // 3 - 1
    elif life < 20:
        return 3
    elif life < 39:
        return 6
    else:
        return 9


def angle(a, b):
    if a == b or b.type == -1:
        return 0
    else:
        u = Pos(x=a.x - base.x, y=a.y - base.y)
        v = Pos(x=b.x - base.x, y=b.y - base.y)
        uv = u.x * v.x + u.y * v.y
        try:
            cosinus = uv/(u.norm()*v.norm())
        except Exception:
            cosinus = 0
        if cosinus > 0:
            cosinus = min(1, cosinus)
        elif cosinus < 0:
            cosinus = max(-1, cosinus)
        return math.acos(cosinus)


def passe(buster):
    target = buster.target
    if actions[buster.state] == 'carry':
        for b in busters:
            if b.type != myTeam or b.i == buster.i or actions[b.state] != 'move' or abs(angle(buster, b)) > math.pi / 8:
                # d(buster.i, b.state, angle(buster, b))
                continue
            # d(buster.i, b.dist(base), buster.dist(base), buster.dist(b))
            if b.dist(base) < buster.dist(base) and (2660 <= buster.dist(b) <= 4400):
                target = b
        fiend_view = False
        for b in busters:
            if b.type == hisTeam and b.dist(target) < view:
                fiend_view = True
        if fiend_view:
            target = buster.target
    return target


def last_carry():
    for b in busters:
        if b.type == myTeam and actions[b.state] == 'carry' and total == secure:
            return b.i
    return False


def full_scan(ex):
    full = True
    for k, v in ex.items():
        if v is False:
            full = False
            break
    if full:
        d('FULL SCAN')
        for k, _ in ex.items():
            ex[k] = False
        # ex[(base.x, base.y)] = True


def move_ghosts():
    for g in ghosts:
        if g.i == -1:
            continue
        loc_bust = [x for x in busters if g.dist(x) <= view]
        if len(loc_bust):
            xm, ym = 0, 0
            for b in loc_bust:
                xm += b.x
                ym += b.y
            xm /= len(loc_bust)
            ym /= len(loc_bust)
            m = Pos(x=xm, y=ym)
            # d(xm, ym, g.dist(m))
            g.escape(m, 400)
            d(g)


def move_fiends():
    for b in busters:
        if b.type == hisTeam and actions[b.state] == 'carry':
            b.move(other, buster_move)
            d('moved ', b.i, b.x, b.y)


class Pos:
    def __init__(self, i=0, x=0, y=0, vx=0, vy=0, range=0):
        self.i = i
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.range = range

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "i{}, x:{} y:{}".format(self.i, self.x, self.y)

    def dist(self, a):
        return math.sqrt((abs(self.x - a.x))**2 + (abs(self.y - a.y))**2)

    def norm(self):
        return math.sqrt(self.x ** 2 + self.y ** 2)

    def canView(self, a):
        return (self.dist(a) <= view)

    def canStun(self, a):
        return (self.dist(a) <= trap_max)

    def canTrap(self, a):
        return (trap_min <= self.dist(a) <= trap_max)

    def near(self, a, b):
        return (self.dist(a) < self.dist(b))

    def move(self, pos, speed):
        d = self.dist(pos)
        d = speed if d <= speed else d
        self.x = int((speed / d) * (pos.x - self.x) + self.x)
        self.y = int((speed / d) * (pos.y - self.y) + self.y)

    def next_pos(self, pos, speed):
        d = self.dist(pos)
        d = speed if d <= speed else d
        return Pos(x=int(speed / d) * (pos.x - self.x) + self.x, y=int(speed / d) * (pos.y - self.y) + self.y)

    def escape(self, pos, speed):
        if self.dist(pos) != 0:
            u = speed / self.dist(pos)
            self.x = int((u + 1) * self.x - u * pos.x)
            self.y = int((u + 1) * self.y - u * pos.y)


class Entity(Pos):
    target = None
    visible = False
    radar = False
    out = False
    power = 20
    tracked = False
    ejected = -1
    esquive = None

    def __init__(self, i=-1, x=0, y=0, type=-1, state=40, value=0):
        super().__init__(i, x, y)
        self.type = type
        # buster state: 0 moving, 1 hasghost, 2 stunned, 3 busting
        # ghost state: stamina
        self.state = state
        # buster value: s = 1 or 3, ghostId; s = 2, number of turns
        # ghost value: number of targets
        self.value = value  # value

    def __str__(self):
        if self.type < 0:
            return 'Ghost {} [{} {}] {} life {} trapping'.format(self.i, self.x, self.y, self.state, self.value)
        else:
            if self.type == myTeam:
                nom = 'Buster'
            else:
                nom = 'Fiend'
            value = ''
            if self.state == 1 or self.state == 3:
                value = 'ghost {}'.format(self.value)
            elif self.state == 2:
                value = 'for {}'.format(self.value)
            return '{} {} {}[{} {}] {} {}'.format(nom, self.i, self.power, self.x, self.y, actions[self.state], value)

    def ghost(self):
        return self.value if self.state == 1 else -1

    def bust_target(self):
        return self.value if self.state == 3 else -1

    def flood(self):
        neighbours = [(1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1)]
        loc = (self.x // 3200, self.y // 3200)
        if len(scanned[self.i]) == nx_max * ny_max:
            scanned[self.i] = set()
        scanned[self.i].add(loc)
        nxt = loc
        visited = [loc]
        # dir = 0 if myTeam == 0 else -1
        while visited:
            pos = visited.pop(0)
            for n in neighbours:
                nxt = a(pos, n)
                if in_bounds(nxt):
                    if nxt in scanned[self.i]:
                        visited.append(nxt)
                    else:
                        scanned[self.i].add(nxt)
                        visited = []
                        break
        d('  from {} found {}'.format(loc, nxt))
        return Entity(x=nxt[0] * 3200, y=nxt[1] * 3200)

    def flood2(self):
        loc = (self.x, self.y)
        if loc in coins:
            p = coins[(coins.index(loc) + 1 + (self.i % 3)) % len(coins)]
        else:
            d, p = 100000, None
            for c in coins:
                if 0 < self.dist(Pos(x=c[0], y=c[1])) < d:
                    d = self.dist(Pos(x=c[0], y=c[1]))
                    p = c
        return Entity(x=p[0], y=p[1])

    def flood3(self):
        val = True if myTeam == 0 else False
        for k in sorted(explored.keys(), reverse=val):
            if explored[k] is False:
                return Entity(x=k[0] * e_range, y=k[1] * e_range)
        return Entity(x=8000, y=4000)

    def ej(self, p):
        t = 901
        if self.dist(p) <= 3460:
            t = 1759
        return Entity(x=int(t / self.dist(p) * (self.x - p.x) + p.x), y=int(t / self.dist(p) * (self.y - p.y) + p.y))

    def play(self):
        global total
        global stunned
        if not self.radar and self.target == view_pos[self.i] and self.dist(self.target) <= buster_move:
            print('RADAR charles-xavier')
            self.radar = True
            self.target = self.flood3()
        elif self.target == base:
            if self.dist(base) <= release_limit and self.state == 1:
                print('RELEASE', '{} release'.format(self.i))
                ghosts[self.value].out = True
                self.target = ghosts[0]
                total += 1
            else:
                if carotte:
                    self.target = self.flood3()
                    print('MOVE {} {} flood'.format(self.target.x, self.target.y))
                elif self.esquive:
                    tgt = self.esquive.i[0] if type(self.esquive.i) is list else self.esquive.i
                    if self.power >= 20 and self.canStun(busters[tgt]):
                        if actions[self.state] == 'carry':
                            self.target = ghosts[self.value]
                        print('STUN {} jean ticipe'.format(tgt))
                    else:
                        xm = self.x if self.x in [x_min, x_max] else self.x + self.esquive.x
                        ym = self.y if self.y in [y_min, y_max] else self.y + self.esquive.y
                        print('MOVE {} {} {} esquive'.format(xm, ym, self.esquive.i))
                else:
                    print('MOVE {} {} {} back home'.format(base.x, base.y, self.i))
        elif type(self.target) is Entity and self.target.type != GHOST:
            if self.target.type == myTeam:
                e = self.ej(self.target)
                print('EJECT {} {} passe {}'.format(e.x, e.y, self.target.i))
                self.ejected = self.value
                self.target = self.flood3()
            elif self.canStun(self.target):
                if self.power == 20:
                    print('STUN {} dans ta gueule'.format(self.target.i))
                    self.power = 0
                    stunned.add(self.target.i)
                    if actions[busters[self.target.i].state] == 'carry' and ghosts[busters[self.target.i].value].i != -1:
                        ghosts[busters[self.target.i].value].out = False
                        ghosts[busters[self.target.i].value].x = self.target.x
                        ghosts[busters[self.target.i].value].y = self.target.y
                        self.target = ghosts[busters[self.target.i].value]
                        self.target.ejected = -2
                elif abs(self.target.dist(other) - release_limit) // buster_move > 20 - self.power:
                    print('MOVE {} {} je taurai'.format(self.target.x, self.target.y))
                else:
                    if self.state == 3:
                        print('BUST {} bust1 {}'.format(self.value, self.value))
                    else:
                        self.target = self.flood3()
                        print('MOVE {} {} trop {} {}'.format(self.target.x, self.target.y, self.target.x, self.target.y))
            else:
                if self.state == 3:
                    print('BUST {} bust2 {}'.format(self.value, self.value))
                elif self.target.state == 3 or self.dist(self.target) <= view:
                    print('MOVE {} {} fume'.format(self.target.x, self.target.y))
                else:
                    # xp, yp = int(2 * self.x - self.target.x), int(2 * self.y - self.target.y)
                    # print('MOVE {} {} cassos'.format(xp, yp))
                    fac = 1.0
                    xp, yp = int(other.x + fac * (self.target.x - self.x)
                                 ), int(other.y + fac * (self.target.y - self.y))
                    print('MOVE {} {} je reste'.format(xp, yp))
        elif self.target:
            if self.target.i == -2:
                print('MOVE {} {} protect {}'.format(self.target.x, self.target.y, self.power))
            elif self.dist(self.target) <= view and self.target != view_pos[self.i]:
                if not self.target.visible:
                    if self.target.i in seen and not self.target.tracked:
                        alpha = (self.dist(self.target) + 2600) / (self.dist(self.target) + 1)
                        # self.target.x = 2 * self.target.x - 1 * self.x
                        self.target.x = int(alpha * (self.target.x - self.x) + self.x)
                        self.target.x = min(x_max, self.target.x)
                        self.target.x = max(x_min, self.target.x)
                        self.target.y = int(alpha * (self.target.y - self.y) + self.y)
                        self.target.y = min(y_max, self.target.y)
                        self.target.y = max(y_min, self.target.y)
                        self.target.state = 40
                        self.target.tracked = True
                        print('MOVE {} {} track {} {} {}'.format(self.target.x,
                                                                 self.target.y, self.target.i, self.target.x, self.target.y))
                    else:
                        ghosts[self.target.i].out = True
                        self.target = self.flood3()
                        print('MOVE {} {} no show {} {}'.format(self.target.x, self.target.y, self.target.x, self.target.y))
                else:
                    if self.canTrap(self.target):
                        print('BUST {} bust3 {}'.format(self.target.i, self.target.i))
                    elif self.dist(self.target) > trap_max:
                        xp = int((self.x - self.target.x) * 1330 / self.dist(self.target) + self.target.x)
                        yp = int((self.y - self.target.y) * 1330 / self.dist(self.target) + self.target.y)
                        print('MOVE {} {} narrow {} {} {}'.format(xp, yp, self.target.i, xp, yp))
                    else:
                        if self.target.i == -2:
                            print('MOVE {} {} still'.format(self.x, self.y))
                        else:
                            self.target = self.flood3()
                            d = self.dist(self.target) + 1
                            xp, yp = int((self.x - self.target.x) * trap_min / d +
                                         self.target.x), int((self.y - self.target.y) * trap_min/d + self.target.y)
                            # print('MOVE {} {} shift {} {}'.format(xp, yp, xp, yp))
                            print('MOVE {} {} shift {} {}'.format(base.x, base.y, xp, yp))
            else:
                if self.x == view_pos[self.i].x and self.y == view_pos[self.i].y:
                    self.target = self.flood3()
                    print('MOVE {} {} explore {} {}'.format(self.target.x, self.target.y, self.target.x, self.target.y))
                else:
                    print('MOVE {} {} hunt {} {} {}'.format(self.target.x,
                                                            self.target.y, self.target.i, self.target.x, self.target.y))
        else:
            self.target = view_pos[self.i]
            print('MOVE {} {} vision {} {} {}'.format(self.target.x,
                                                      self.target.y, self.target.i, self.target.x, self.target.y))


def settings(nbVisible):
    global bust_list
    global carried
    for g in ghosts:
        g.visible = True if g.ejected == -2 else False
        g.ejected = -1
    for b in busters:
        b.visible = False
    # Update informations from play
    for e in range(nbVisible):
        # Save, update Busters & Ghosts
        e = Entity()
        e.i, e.x, e.y, e.type, e.state, e.value = [int(j) for j in input().split()]
        e.visible = True
        if e.type == GHOST:
            # if e.i in seen:
            #     e.out = ghosts[e.i].out
            # else:
            e.out = False
            e.tracked = ghosts[e.i].tracked
            ghosts[e.i] = e
            seen.add(e.i)
            sym_id = (e.i + 1 - 2 * myTeam) % nbGhosts
            # La distribution des fantômes est symétrique
            if ghosts[sym_id].x == x_max and sym_id not in seen and nbTurn < 20:
                xs, ys = 2 * int(x_max/2) - e.x, 2 * int(y_max/2) - e.y
                ghosts[sym_id] = Entity(i=sym_id, x=xs, y=ys, state=e.state)
        else:
            e.radar = busters[e.i].radar
            e.power = busters[e.i].power
            e.ejected = busters[e.i].ejected
            if actions[e.state] == 'carry':
                e.target = base
                carried.add(e.value)
            else:
                e.target = busters[e.i].target
            if e.power < 20:
                e.power += 1
            busters[e.i] = e
            if actions[e.state] == 'bust':
                if e.bust_target() in bust_list[e.type]:
                    bust_list[e.type][e.bust_target()] += 1
                else:
                    bust_list[e.type][e.bust_target()] = 1
        d(e)
    for k, v in bust_list[myTeam].items():
        if ghosts[k].value > v and k not in bust_list[hisTeam]:
            bust_list[hisTeam][k] = ghosts[k].value - v


def bestTarget(buster):
    global bust_list
    global carried, total, secure, la_passe
    can_bust = [1] * nbGhosts
    for g in ghosts:
        for b in busters:
            if b.i != buster.i and b.visible and b.canTrap(g):
                can_bust[g.i] += 1

    if la_passe[0] != -1 and buster.i == la_passe[1] and ghosts[la_passe[0]].visible:
        return ghosts[la_passe[0]]
    score = 100000
    if not buster.radar and len(seen) < .6 * nbGhosts:
        target = view_pos[buster.i]
        score = buster.dist(target) // buster_move + target.state + 3
    else:
        target = buster.target
    sorted_ghosts = sorted(ghosts, key=lambda g: not g.visible)
    for g in sorted_ghosts:
        # d( '   ', g, g.dist(buster), g.visible, g.out)
        if g.dist(buster) <= view and not g.visible:
            g.out = True
            continue
        if total == secure and not g.out and g.i != -1:
            target = g
            break
            # or (g.i in bust_list[myTeam] and g.value == 1 and buster.bust_target() != g.i and g.i not in bust_list[hisTeam]) \
            # and g.i not in bust_list[hisTeam]) \
        if g.out or g.i in carried or g.i == -1 \
                or ((nbBusters > 2) and g.value > 0 and g.state // g.value <= (g.dist(buster) - trap_max) // buster_move) \
                or g.i == buster.ejected or (la_passe[0] != -1 and la_passe[0] == g.i and la_passe[1] != buster.i):
            continue
        beta = norm_life(g.state) if total >= secure else g.state
        cost = can_bust[g.i] * (g.dist(buster) // buster_move) + beta
        cost = 1 * (g.dist(buster) // buster_move) + beta
        d(' s {} - {} G#{}'.format(score, cost, g.i))
        if cost < score:
            target = g
            score = cost
            # if total == secure - 1:
            # g.state += 40
    return target


def defense(buster, to_stun):
    global stunned
    target = buster.target
    same_loc = False
    visi_ghosts = 0
    type_def = -1
    for g in ghosts:
        if g.x == buster.x and g.y == buster.y:
            same_loc = True
        if g.visible:
            visi_ghosts += 1
    for b in busters:
        if b.type != hisTeam or b.i in stunned or (b.i in to_stun and total < secure):
            continue
        d('   f', b.i, b.state, buster.power,  buster.state, int(b.dist(other)), int(buster.dist(other)))
        if ghosts[buster.bust_target()].value > 1:
            threshold = ghosts[buster.bust_target()].value - 1
        else:
            threshold = 1
        # Take advantage if we are on the same ghost
        if b.visible and buster.power == 20 and actions[buster.state] == 'bust' and actions[b.state] != 'stun' \
                and b.bust_target() == buster.bust_target() and b.dist(buster) <= view \
                and buster.target.value >= 2 and 0 <= ghosts[buster.bust_target()].state < 9 * threshold:
            target = b
            type_def = 0
        # Stealing
        if actions[buster.state] == 'move' and actions[b.state] == 'carry' and buster.power + b.dist(other) // buster_move >= 20 and (buster.dist(other) - trap_max < b.dist(other) or b.dist(buster) <= trap_max):
            target = b
            type_def = 1
        # Real defense
        if b.visible and actions[buster.state] in ['bust', 'carry'] and b.dist(buster) <= trap_max and buster.power == 20 and actions[b.state] in ['move', 'bust']:
            target = b
            type_def = 2
        # just after double busting while carrying
        if b.visible and same_loc and buster.canStun(b) and actions[b.state] != 'stun':
            target = b
            type_def = 3
        # busting defense +
        if b.visible and actions[buster.state] == 'bust' and buster.target.state < 9 and buster.power == 20 and b.dist(buster) <= trap_max:
            target = b
            type_def = 4
        # nearly the end = bourin
        if type_def == -1 and b.visible and actions[buster.state] != 'carry' and total == secure and actions[b.state] != 'stun' and visi_ghosts == 0:
            target = b
            type_def = 5
    d('defense', type_def)
    return target


def esquive(buster):
    # if abs(buster.x - base.x) < 300 or abs(buster.y - base.y) < 300:
    #    return Pos(x=base.x - buster.x, y=base.y - buster.y)
    b_list = []
    fact = 1.5
    for b in busters:
        if b.visible and (b.type == hisTeam) and actions[b.state] != 'stun' and buster.dist(b) <= 2.0*view and b.dist(base) - release_limit < buster.dist(base):
            b_list.append(b)
    if b_list:
        xb, yb, ind = 0, 0, []
        for b in b_list:
            xb += b.x
            yb += b.y
            ind.append(b.i)
        xb /= len(b_list)
        yb /= len(b_list)
        return Pos(i=ind, x=int(base.x + fact * (buster.x - xb)), y=int(base.y + fact * (buster.y - yb)))
    else:
        return None


###################
# This is the MAIN
###################
nbBusters = int(input())  # the amount of busters you control
nbGhosts = int(input())  # the amount of ghosts on the map
myTeam = int(input())
hisTeam = 1 if myTeam == 0 else 0
global total, secure, carotte
total, secure, carotte = 0, nbGhosts // 2, False
seen = set()
fill = [(i, j) for j in range(3) for i in range(5)]
scanned = [set()] * 2 * nbBusters
base, other = Entity(x=0, y=0), Entity(x=x_max, y=y_max)
if myTeam == 1:
    base, other = other, base
    fill.reverse()
e_range = 2500
ex_max, ey_max = x_max // e_range, y_max // e_range
explored = {(i, j): False for i in range(ex_max + 1) for j in range(ey_max + 1)}
# explored[(base.x, base.y)] = True
sym = 1 - 2 * myTeam
busters = 2 * nbBusters * [Entity()]
fiends = nbBusters * [Entity()]
ghosts = nbGhosts * [Entity(x=other.x, y=other.y)]
view_pos = dict()
nbTurn = 0

if 2 * int(nbGhosts / 2) != nbGhosts:
    ghosts[0] = Entity(i=0, x=int(x_max/2), y=int(y_max/2), state=4)
weaks = [False] * nbBusters * 2
weak_life = 40
global carried, bust_list, stunned, la_passe
la_passe = [-1, -1]

# game loop
while True:
    nbTurn += 1
    nbVisible = int(input())
    bust_list = [dict(), dict()]
    stunned = set()
    carried = set()
    settings(nbVisible)
    init_pos()
    treat_weaks()
    last_one = last_carry()
    carotte = la_carotte(carotte)
    if la_passe[0] != -1 and ghosts[la_passe[0]].out:
        la_passe = [-1, -1]
    d(nbTurn, last_one, total, secure, carotte, seen, carried, bust_list, stunned)

    # Define actions of Busters
    to_stun = []
    for buster in busters:
        if buster.type != myTeam:
            continue
        tup = (buster.x // e_range, buster.y // e_range)
        explored[tup] = True
        if buster.ejected != -1 and not ghosts[buster.ejected].visible:
            buster.ejected = -1
        if weaks[buster.i]:
            d('buster{} {}'.format(buster.i, buster.ejected))
            if buster.target != base:
                buster.target = bestTarget(buster)
                if last_one is not False and buster.i != last_one:
                    last = busters[last_one]
                    buster.target = Entity(i=-2, x=last.x, y=last.y)
                buster.target = defense(buster, to_stun)
            else:
                buster.target = passe(buster)
                buster.target = defense(buster, to_stun)
                buster.esquive = esquive(buster)
                if buster.target.type == myTeam:
                    la_passe = [buster.value, buster.target.i]
                    moi = Entity(x=busters[la_passe[1]].x, y=busters[la_passe[1]].y)
                    moi.visible = True
                    moi.i = -2
                    busters[la_passe[1]].target = moi
        if type(buster.target) is Entity and buster.target.type == hisTeam:
            to_stun.append(buster.target.i)
    full_scan(explored)
    # d(explored)
    # Play actions
    for buster in busters:
        if buster.type != myTeam:
            continue
        if buster.target:
            d(buster.i, ' selected target', buster.target, buster.target.ejected)
        if buster.target and buster.target.type == -1 and buster.target.i == -1:
            tup = (buster.target.x // e_range, buster.target.y // e_range)
            explored[tup] = True
        if actions[buster.state] == 'stun':
            buster.target = view_pos[buster.i]
            print('MOVE 0 0')
        else:
            buster.play()
        if buster.dist(view_pos[buster.i]) < buster_move and not weaks[buster.i]:
            d('update weak NOW', buster.i)
            weak_life += 1
    move_ghosts()
    move_fiends()
