#!/usr/bin/env python3
"""Rubellite Rings — neon hoop-thread arcade for ElbowOS."""
from __future__ import annotations

import math
import os
import random
import subprocess
import sys

import pygame

W, H = 1080, 1920
FPS = 30
TITLE = "RUBELLITE RINGS"
HANDLE = "x.com/ElbowOS"
BG = (18, 4, 22)
WINE = (86, 10, 38)
INK = (255, 236, 246)
RUBY = (255, 48, 110)
PINK = (255, 120, 170)
MINT = (80, 255, 210)
GOLD = (255, 214, 90)
IVORY = (255, 244, 230)
VIOLET = (150, 60, 220)


class Spark:
    __slots__ = ("x", "y", "vx", "vy", "life", "col", "r")

    def __init__(self, x, y, vx, vy, life, col, r=5):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life, self.col, self.r = life, col, r


class Ring:
    __slots__ = ("y", "cx", "amp", "ph", "spd", "r_out", "r_in", "spin", "hue", "hit")

    def __init__(self, y):
        self.y = y
        self.cx = W * 0.5
        self.amp = random.uniform(140, 280)
        self.ph = random.random() * 6.283
        self.spd = random.uniform(0.7, 1.6) * random.choice((-1, 1))
        self.r_out = random.randint(92, 128)
        self.r_in = self.r_out - random.randint(26, 36)
        self.spin = random.uniform(1.2, 2.8)
        self.hue = random.choice((RUBY, PINK, MINT, GOLD, VIOLET))
        self.hit = False

    @property
    def x(self):
        return self.cx + math.sin(self.ph) * self.amp


class Game:
    def __init__(self, record: bool):
        self.record = record
        self.surf = pygame.Surface((W, H))
        self.clock = pygame.time.Clock()
        self.font_lg = pygame.font.Font(None, 70)
        self.font_md = pygame.font.Font(None, 48)
        self.font_sm = pygame.font.Font(None, 32)
        self.reset()

    def reset(self) -> None:
        self.px, self.py = W * 0.5, H * 0.68
        self.pvx = 0.0
        self.score = getattr(self, "score", 0) if getattr(self, "keep_score", False) else 0
        self.keep_score = True
        self.combo = 0
        self.pulse = 0.0
        self.flash = 0.0
        self.t = 0.0
        self.fall = 420.0
        self.sparks: list[Spark] = []
        self.petals = [
            [random.uniform(0, W), random.uniform(0, H), random.uniform(18, 46),
             random.choice((WINE, (60, 8, 30), (40, 6, 28)))]
            for _ in range(28)
        ]
        self.rings = [Ring(-i * 280 - 80) for i in range(8)]

    def burst(self, x, y, col, n=14) -> None:
        for _ in range(n):
            a = random.random() * 6.283
            spd = random.uniform(80, 460)
            self.sparks.append(Spark(x, y, spd * math.cos(a), spd * math.sin(a),
                                     random.uniform(0.18, 0.55), col, random.randint(3, 8)))

    def autoplay(self, _dt: float) -> None:
        nxt = None
        best = 1e9
        for r in self.rings:
            dy = self.py - r.y
            if 40 < dy < 820 and dy < best:
                best, nxt = dy, r
        if nxt:
            err = nxt.x - self.px
            self.pvx += max(-28, min(28, err * 0.085))
        self.pvx += 9.0 * math.sin(self.t * 2.4)

    def update(self, dt: float) -> None:
        self.pulse += dt
        self.t += dt
        self.flash = max(0.0, self.flash - dt)
        self.fall = 380 + 90 * math.sin(self.t * 0.35) + self.combo * 6
        if self.record:
            self.autoplay(dt)
        else:
            keys = pygame.key.get_pressed()
            acc = 980
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.pvx -= acc * dt
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.pvx += acc * dt
        self.pvx *= 0.90
        self.px += self.pvx * dt
        self.px = max(90, min(W - 90, self.px))

        for p in self.petals:
            p[1] += (40 + p[2]) * dt
            if p[1] > H + 20:
                p[0], p[1] = random.uniform(0, W), -30

        for r in self.rings:
            r.y += self.fall * dt
            r.ph += r.spd * dt
            r.spin += dt * 2.2
            if r.y > H + 160:
                r.__init__(-180 - random.uniform(0, 90))
                continue
            dx, dy = self.px - r.x, self.py - r.y
            dist = math.hypot(dx, dy)
            if (not r.hit) and abs(dy) < 22:
                if dist <= r.r_in - 6:
                    r.hit = True
                    self.combo += 1
                    self.score += 12 + self.combo * 3
                    self.flash = 0.18
                    self.burst(r.x, r.y, r.hue, 18)
                elif dist < r.r_out + 16:
                    r.hit = True
                    self.combo = 0
                    self.score = max(0, self.score - 8)
                    self.flash = 0.28
                    self.burst(self.px, self.py, RUBY, 22)
                    self.px += random.choice((-1, 1)) * 70

        alive = []
        for sp in self.sparks:
            sp.life -= dt
            if sp.life <= 0:
                continue
            sp.x += sp.vx * dt
            sp.y += sp.vy * dt
            alive.append(sp)
        self.sparks = alive

    def handle(self, ev) -> None:
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_r:
            self.keep_score = False
            self.reset()

    def draw(self, s: pygame.Surface) -> None:
        s.fill(BG)
        for i in range(16):
            y = int((self.pulse * 55 + i * 140) % (H + 40)) - 20
            pygame.draw.line(s, (36, 8, 42), (0, y), (W, y), 2)
        for x, y, r, col in self.petals:
            pygame.draw.circle(s, col, (int(x), int(y)), int(r))

        pygame.draw.rect(s, (40, 6, 28), (36, 210, W - 72, H - 330), border_radius=28)
        pygame.draw.rect(s, PINK, (36, 210, W - 72, H - 330), 4, border_radius=28)

        order = sorted(self.rings, key=lambda rr: rr.y)
        for r in order:
            x, y = int(r.x), int(r.y)
            glow = 4 + int(6 * (0.5 + 0.5 * math.sin(r.spin)))
            pygame.draw.circle(s, r.hue, (x, y), r.r_out + glow, 3)
            pygame.draw.circle(s, r.hue, (x, y), r.r_out, 10)
            pygame.draw.circle(s, IVORY if r.hit else (255, 180, 210), (x, y), r.r_out, 3)
            pygame.draw.circle(s, BG, (x, y), r.r_in)
            pygame.draw.circle(s, r.hue, (x, y), r.r_in, 2)
            for k in range(6):
                a = r.spin + k * math.pi / 3
                x1 = x + int(math.cos(a) * (r.r_in + 4))
                y1 = y + int(math.sin(a) * (r.r_in + 4))
                x2 = x + int(math.cos(a) * (r.r_out - 4))
                y2 = y + int(math.sin(a) * (r.r_out - 4))
                pygame.draw.line(s, IVORY, (x1, y1), (x2, y2), 2)

        px, py = int(self.px), int(self.py)
        glow = 10 + int(6 * math.sin(self.pulse * 8))
        pygame.draw.circle(s, (255, 80, 140), (px, py), 28 + glow)
        pygame.draw.circle(s, RUBY, (px, py), 24)
        pygame.draw.circle(s, PINK, (px, py), 24, 3)
        pygame.draw.circle(s, IVORY, (px - 7, py - 8), 6)
        pygame.draw.circle(s, (180, 20, 70), (px, py + 34), 10)

        for sp in self.sparks:
            pygame.draw.circle(s, sp.col, (int(sp.x), int(sp.y)), max(1, int(sp.r * sp.life * 2)))

        title = self.font_lg.render(TITLE, True, PINK)
        s.blit(title, title.get_rect(center=(W // 2, 64)))
        handle = self.font_sm.render(HANDLE, True, MINT)
        s.blit(handle, handle.get_rect(center=(W // 2, 114)))
        score = self.font_md.render(f"SCORE  {self.score}    STREAK  {self.combo}", True, GOLD)
        s.blit(score, score.get_rect(center=(W // 2, 172)))
        hint = self.font_sm.render("A / D thread the hoops    R reset    x.com/ElbowOS", True, MINT)
        s.blit(hint, hint.get_rect(center=(W // 2, H - 48)))
        if self.flash > 0:
            flash = pygame.Surface((W, H), pygame.SRCALPHA)
            flash.fill((255, 70, 140, int(90 * self.flash / 0.28)))
            s.blit(flash, (0, 0))

    def play(self) -> None:
        screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption(TITLE)
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                    running = False
                else:
                    self.handle(ev)
            self.update(dt)
            self.draw(self.surf)
            screen.blit(self.surf, (0, 0))
            pygame.display.flip()

    def record_mp4(self, path: str) -> None:
        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
            "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "20", "-preset", "fast", "-movflags", "+faststart", path,
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        frames = FPS * 15
        for i in range(frames):
            self.update(1.0 / FPS)
            self.draw(self.surf)
            proc.stdin.write(pygame.image.tostring(self.surf, "RGB"))
            if i % 30 == 0:
                print(f"frame {i}/{frames}", flush=True)
        proc.stdin.close()
        rc = proc.wait()
        if rc != 0:
            raise SystemExit(f"ffmpeg failed: {rc}")
        print("wrote", path)


def main() -> None:
    record = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
    play = "--play" in sys.argv
    if record or not play:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    pygame.init()
    pygame.font.init()
    g = Game(record or not play)
    if record or not play:
        out = os.environ.get("ELBOWOS_MP4", "/home/workdir/artifacts/RUBELLITE_RINGS_ElbowOS.mp4")
        g.record_mp4(out)
    else:
        g.play()
    pygame.quit()


if __name__ == "__main__":
    main()
