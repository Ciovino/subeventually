# Vision

## The problem

Timers tell cubers *how long* a solve took, but not *why*. To improve, a cuber has to work out alone where time was lost: a poor cross choice, an inefficient F2L pair, a multi-look last layer. They also have to guess which of the hundreds of available algorithms is actually worth learning next.

## The idea

subeventually is a self-hosted platform for tracking and improving at speedcubing.
Its core is a **cubing assistant** that, for every solve:

1. computes the best solve achievable **with the full algorithm set** of a method;
2. computes the best solve achievable **with the player's own repertoire**;
3. compares both with what the player did (as precisely as the player cares to describe it) and attributes the lost time to execution, planning or knowledge;
4. ranks unknown algorithms by the time they would save.

"Best" is measured in estimated seconds, personalized with the player's own execution times, not in move count.

## Principles

- **Self-hosted first:** your solves and data stay on your server.
- **Extensible:** methods, algorithm sets and (later) puzzles are plugins or data files.
- **Low friction:** quick, skippable questions by default; detailed input is optional.
- **Data-driven:** raw solve data is kept, so analyses and models can improve over time.

## Phases

### Phase 1: Terminal assistant (current)

A terminal app for 3x3. Configure a method and the algorithms you know, measure your execution times, enter a scramble, get the analysis. Analyses are stored locally.

### Phase 2: Server and web app

A Python server with database and accounts, random-state scramble generation (with optional editing), a timer web app with sessions and statistics, and leaderboards (excluding solves with edited scrambles). The assistant runs server-side. Deployed with Docker Compose.

### Phase 3: Expansion

More puzzles, smarter assistant features (machine learning, long-term solve analysis), smart-cube support over Bluetooth, possibly a versus mode, and a refreshed interface.

### Phase 4: Android app

An offline-first mobile app that syncs with a self-hosted server when available.

## Non-goals (for now)

- Puzzles other than 3x3 before Phase 3.
- Truly optimal solving: the assistant works within the rules of a method.
- Real-time move tracking before smart-cube support exists.
