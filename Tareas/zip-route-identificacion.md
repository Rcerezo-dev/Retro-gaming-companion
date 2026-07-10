# ZIP-ROUTE — Identificación de los ZIPs sueltos de `Unknown\` (2026-07-10)

Identificación por CRC32 del header ZIP (sin descomprimir): entradas de cada
ZIP cruzadas contra los DATs No-Intro/Redump (`CatalogEntry.crc32`,
`catalog_loader.py:104`) y contra MAME 0.286 + FBNeo arcade (votación por
cobertura de sets). Fuente: junk-scan de Día40 (56 colecciones + 208
"ZIPs no-ROM" + 5 arcade sin organizar = 269 ZIPs).

| Grupo | ZIPs | Acción propuesta |
|-------|------|------------------|
| A. Juegos de consola (CRC exacto en DAT) | 95 | renombrar a nombre canónico + mover a carpeta de plataforma |
| B. Sets arcade identificados al 100 % | 79 | renombrar al nombre de set + mover a `arcade\` |
| C. Sets arcade probables (match parcial) | 29 | review con sugerencia (otra versión de romset) |
| D. Romhacks / traducciones (1 ROM, sin CRC) | 49 | mover a carpeta de plataforma (por extensión interna) conservando nombre |
| E. Colecciones reales (zip-de-zips / .chd) | 16 | extraer al Inbox → pipeline existente |
| F. Resto sin identificar | 1 | review manual |

## A. Juegos de consola con match CRC exacto

| ZIP | Título canónico | DAT |
|-----|-----------------|-----|
| A Bug's Life (TW).zip | Bug's Life, A - Chong Chong Weiji (Taiwan) (En) (Unl) | Sega - Mega Drive - Genesis |
| A Dinosaur's Tale (NA).zip | Dinosaur's Tale, A (USA) | Sega - Mega Drive - Genesis |
| AWS Pro Moves Soccer (NA).zip | Pro Moves Soccer (USA) | Sega - Mega Drive - Genesis |
| Actraiser (Japan) (9-12).zip | ActRaiser (USA) | Nintendo - Super Nintendo Entertainment System |
| Adventure (Europe).zip | Super Pocket - The Atari Collection (World) (Extracted) | Blaze Entertainment - Evercade |
| Adventurous Boy - Mao Xian Xiao Zi (TW).zip | Adventurous Boy - Maoxian Xiaozi (Taiwan) (En) (Unl) | Sega - Mega Drive - Genesis |
| Air Buster - Trouble Specialty Raid Unit (NA).zip | Air Buster (USA) | Sega - Mega Drive - Genesis |
| Arcus Odyssey (Japan) (Mega Drive).zip | Arcus Odyssey (USA) | Sega - Mega Drive - Genesis |
| Arkanoid (USA).zip | Arkanoid (USA) | Nintendo - Nintendo Entertainment System (Headered) |
| Arkanoid - Doh It Again (Japan) (En) (4-12) [b].zip | Arkanoid - Doh It Again (USA) | Nintendo - Super Nintendo Entertainment System |
| Art Alive! (NA).zip | Art Alive (World) | Sega - Mega Drive - Genesis |
| Asteroids (USA).zip | Asteroids (Japan, USA) (En) | Atari - Atari 2600 |
| Aworg (JP).zip | Aworg - Hero in the Sky (Japan) (Sega Game Toshokan) | Sega - Mega Drive - Genesis |
| Aztec Adventure ~ Nazca '88 - The Golden Road to Paradise (World).zip | Aztec Adventure (World) | Sega - Master System - Mark III |
| Ballz 3D - Fighting at Its Ballziest ~ Ballz 3D - The Battle of the Ballz (USA, Europe).zip | Ballz 3D - The Battle of the Ballz (USA, Europe) | Sega - Mega Drive - Genesis |
| Banjo-Kazooie (World) (XBLA).zip | Banjo-Kazooie (USA) (Rev 1) | Nintendo - Nintendo 64 (BigEndian) |
| Banjo-Tooie (World) (XBLA).zip | Banjo-Tooie (USA) | Nintendo - Nintendo 64 (BigEndian) |
| Bare Knuckle - Ikari no Tekken ~ Streets of Rage (World) (Rev A).zip | Streets of Rage (World) (Rev A) | Sega - Mega Drive - Genesis |
| Blackthorne (World) (Windows).zip | Blackthorne (USA) | Nintendo - Super Nintendo Entertainment System |
| Bubble Ghost (USA).zip | Bubble Ghost (USA, Europe) | Nintendo - Game Boy |
| California Games (USA).zip | California Games (USA) | Atari - Atari 2600 |
| California Games ~ Jogos de Verao (USA, Europe, Brazil).zip | California Games (USA, Europe, Brazil) (En) | Sega - Master System - Mark III |
| Cannon Fodder (United Kingdom) (Disk 1).zip | Cannon Fodder (Europe) | Nintendo - Super Nintendo Entertainment System |
| Castle of Illusion Starring Mickey Mouse (World) (584112C7) (Addon).zip | Castle of Illusion Starring Mickey Mouse (USA, Europe) | Sega - Mega Drive - Genesis |
| Centipede (Europe).zip | Centipede (Japan, USA) (En) | Atari - Atari 2600 |
| Chuck Rock (United Kingdom) (Disk 1).zip | Chuck Rock (USA) | Nintendo - Super Nintendo Entertainment System |
| Comix Zone (World) (En,Ja,Fr,De,Es,It) (XBLA).zip | Comix Zone (USA) | Sega - Mega Drive - Genesis |
| Coryoon - Child of Dragon (Japan).zip | Coryoon (Japan) | NEC - PC Engine - TurboGrafx-16 |
| Daimakaimura ~ Ghouls'n Ghosts (Japan, USA).zip | Ghouls'n Ghosts (Japan, USA) (En,Ja) | Sega - Mega Drive - Genesis |
| Deja Vu (USA) (Disk 1).zip | Deja Vu (USA) | Nintendo - Nintendo Entertainment System (Headered) |
| Dig Dug (Disk 1) (Unknown) (Side A).zip | Dig Dug (USA) | Atari - Atari 2600 |
| Download (Japan).zip | Down Load (Japan) | NEC - PC Engine - TurboGrafx-16 |
| Dr. Robotnik's Mean Bean Machine (USA).zip | Dr. Robotnik's Mean Bean Machine (USA) | Sega - Mega Drive - Genesis |
| DuckTales (World) (42560829) (Addon).zip | DuckTales (USA) | Nintendo - Nintendo Entertainment System (Headered) |
| Ecco the Dolphin (World) (En,Ja,Fr,De,Es,It) (XBLA).zip | Ecco the Dolphin (USA, Europe, Korea) (En) | Sega - Mega Drive - Genesis |
| Elite (Europe).zip | Elite (Europe) (En,Fr,De) | Nintendo - Nintendo Entertainment System (Headered) |
| Fatal Fury Special (World) (En,Ja) (XBLA).zip | Fatal Fury Special (USA) | Nintendo - Super Nintendo Entertainment System |
| Firemen, The (Japan) (2-9).zip | Firemen, The (Europe) (En,Fr,De) | Nintendo - Super Nintendo Entertainment System |
| Flicky (Japan) [b].zip | Flicky (USA, Europe) | Sega - Mega Drive - Genesis |
| Frogger (USA).zip | Frogger (USA) | Atari - Atari 2600 |
| Granada (Japan) (Rev 1) (X68000).zip | Granada (Japan, USA) (En) (Rev A) | Sega - Mega Drive - Genesis |
| Gravitar (USA).zip | Super Pocket - The Atari Collection (World) (Extracted) | Blaze Entertainment - Evercade |
| Gunstar Heroes (World) (XBLA).zip | Gunstar Heroes (Japan) | Sega - Game Gear |
| Hammer Lock Wrestling (USA).zip | Hammerlock Wrestling (USA) | Nintendo - Super Nintendo Entertainment System |
| Image Fight (Japan).zip | ImageFight (Japan) (En) | NEC - PC Engine - TurboGrafx-16 |
| Joust (USA).zip | Joust (USA) | Atari - Atari 2600 |
| Kaboom! (USA, Europe).zip | Kaboom! (USA) | Atari - Atari 2600 |
| Kung Fu (Europe).zip | Kung Fu (Japan, USA) (En) | Nintendo - Nintendo Entertainment System (Headered) |
| Lock n' Chase ~ Lock 'n' Chase (World).zip | Lock n' Chase (World) | Nintendo - Game Boy |
| Master of Monsters (Japan) (PC-8801).zip | Master of Monsters (USA) | Sega - Mega Drive - Genesis |
| Mega Man (World) (583607D3) (Addon).zip | Mega Man (USA) | Nintendo - Nintendo Entertainment System (Headered) |
| Metal Gear Solid (World) (4B4E083C) (Addon).zip | Metal Gear Solid (USA) | Nintendo - Game Boy Color |
| Missile Command (USA).zip | Missile Command (USA) | Atari - Atari 2600 |
| Mission Impossible (Japan).zip | Mission - Impossible (USA) (En,Fr,Es) | Nintendo - Game Boy Color |
| Motoracer Advance (USA) (En,Fr,De,Es,It).zip | Moto Racer Advance (USA) (En,Fr,De,Es,It) | Nintendo - Game Boy Advance |
| Ninja Five-0 (USA).zip | Ninja Five-O (USA) | Nintendo - Game Boy Advance |
| Ninja Gaiden II - The Dark Sword of Chaos (Prototype 8-15-91) (Unknown) (3.5 inch).zip | Ninja Gaiden II - The Dark Sword of Chaos (USA) | Nintendo - Nintendo Entertainment System (Headered) |
| Out of This World (USA) (Disk 1).zip | Out of This World (USA) | Nintendo - Super Nintendo Entertainment System |
| Palamedes (Japan).zip | Palamedes (USA) | Nintendo - Nintendo Entertainment System (Headered) |
| Perfect Dark (World) (Beta) (XBLA).zip | Perfect Dark (USA) (Rev 1) | Nintendo - Nintendo 64 (BigEndian) |
| Phantasy Star II (World) (XBLA).zip | Phantasy Star II (USA, Europe) (Rev A) | Sega - Mega Drive - Genesis |
| Pirates! (Disk 1) (Unknown) (Side A).zip | Pirates! (USA) | Nintendo - Nintendo Entertainment System (Headered) |
| Populous (United Kingdom).zip | Populous (Japan) (En) | NEC - PC Engine - TurboGrafx-16 |
| Putty Squad (World) (XBLA).zip | Putty Squad (Europe) | Nintendo - Super Nintendo Entertainment System |
| Qix (USA).zip | QIX (USA) | Nintendo - Nintendo Entertainment System (Headered) |
| River Raid (USA, Europe).zip | River Raid (USA) | Atari - Atari 2600 |
| Rock N' Roll Racing (World).zip | Rock N' Roll Racing (USA) | Nintendo - Super Nintendo Entertainment System |
| Shadowgate (USA) (Disk 1).zip | Shadowgate (USA) | Nintendo - Nintendo Entertainment System (Headered) |
| Shanghai II - Dragon's Eye (USA) (Disk 1).zip | Shanghai II - Dragon's Eye (USA) | Nintendo - Super Nintendo Entertainment System |
| SimCity (United Kingdom).zip | SimCity (USA) | Nintendo - Super Nintendo Entertainment System |
| Sky Kid (Japan) (En).zip | Sky Kid (USA) | Nintendo - Nintendo Entertainment System (Headered) |
| Skyblazer (Japan, USA) (En).zip | Skyblazer (USA) | Nintendo - Super Nintendo Entertainment System |
| Solaris (USA).zip | Super Pocket - The Atari Collection (World) (Extracted) | Blaze Entertainment - Evercade |
| Sonic Blast Man (Japan).zip | Sonic Blast Man (USA) | Nintendo - Super Nintendo Entertainment System |
| Sonic The Hedgehog (World) (XBLA).zip | Sonic The Hedgehog (World) (Rev A) | Sega - Game Gear |
| Sonic The Hedgehog 2 (World) (XBLA).zip | Sonic The Hedgehog 2 (Europe, Brazil) (En) (Rev 1) | Sega - Master System - Mark III |
| Space Invaders (World) (Erwin's Collection).zip | Space Invaders (USA) | Atari - Atari 2600 |
| Streets of Rage 2 (USA).zip | Streets of Rage 2 (USA) | Sega - Mega Drive - Genesis |
| Streets of Rage 2 (World) (XBLA).zip | Streets of Rage 2 (World) | Sega - Game Gear |
| Super Bomberman (Japan) (En) (5-3).zip | Super Bomberman (USA) | Nintendo - Super Nintendo Entertainment System |
| Super Bomberman 2 (Japan) (En) (8-17).zip | Super Bomberman 2 (USA) | Nintendo - Super Nintendo Entertainment System |
| Super Breakout (USA).zip | Super Breakout (USA) | Atari - Atari 2600 |
| Tapper (Disk 1) (Unknown) (Side A).zip | Tapper (USA) | Atari - Atari 2600 |
| Tatsujin ~ Truxton (World).zip | Truxton (World) | Sega - Mega Drive - Genesis |
| Tetris (USA).zip | Tetris (USA) | Nintendo - Nintendo Entertainment System (Headered) |
| Tomb Raider (World) (53510802) (Addon).zip | Tomb Raider (USA, Europe) (En,Fr,De,Es,It) | Nintendo - Game Boy Color |
| Tony Hawk's Pro Skater 2 (USA).zip | Tony Hawk's Pro Skater 2 (USA, Europe) | Nintendo - Game Boy Advance |
| Tony Hawk's Pro Skater 4 (USA) (Zodiac).zip | Tony Hawk's Pro Skater 4 (USA, Europe) | Nintendo - Game Boy Advance |
| Ultimate Mortal Kombat 3 (World) (XBLA).zip | Ultimate Mortal Kombat 3 (USA) | Nintendo - Super Nintendo Entertainment System |
| Video Pinball ~ Arcade Pinball (USA).zip | Super Pocket - The Atari Collection (World) (Extracted) | Blaze Entertainment - Evercade |
| Warlords (Unknown) (Disk 1).zip | Warlords (USA) | Atari - Atari 2600 |
| Where In The World Is Carmen Sandiego (Disk 1) (Unknown) (Side A).zip | Where in the World Is Carmen Sandiego (USA) (En,Fr,De,Es,It) | Nintendo - Super Nintendo Entertainment System |
| Wild Guns (Japan).zip | Wild Guns (USA) | Nintendo - Super Nintendo Entertainment System |
| Worms Armageddon (USA) (Press Kit) (Mac).zip | Worms Armageddon (USA) (En,Fr,Es) | Nintendo - Nintendo 64 (BigEndian) |
| Worms World Party (USA) (ARM).zip | Worms - World Party (USA) (En,Fr,De,Es,It) | Nintendo - Game Boy Advance |

## B. Sets arcade identificados al 100 %

| ZIP | Set correcto (cobertura) |
|-----|--------------------------|
| 1943 (World) (Erwin's Collection).zip | 1943u (37/37) |
| 3wonderu.zip | 3wondersu (19/19) |
| Asylum (Europe) (Disk 1).zip | asylum (29/29) |
| Blitz (Europe).zip | blitz (5/5) |
| Bubbles (World).zip | bubbles (13/13) |
| Columns (USA).zip | columns (2/2) |
| Conquest (World) (XBLIG).zip | conquest (5/5) |
| Dogpatch (USA).zip | dogpatch (4/4) |
| Galaxian (Europe).zip | galaxian (8/8) |
| Genix (World) (XBLIG).zip | genix (11/11) |
| Guwange (World) (XBLA).zip | guwange (10/10) |
| Horizon (Japan).zip | horizon (21/21) |
| Invaders (World) (Erwin's Collection).zip | invaders (4/4) |
| Ixion (United Kingdom) (Disk 1).zip | ixion (19/19) |
| JoyJoy (World).zip | joyjoy (7/7) |
| Lemmings (United Kingdom).zip | lemmings (16/16) |
| Mappy (Japan) (En).zip | mappy (11/11) |
| Maze (USA).zip | maze (2/2) |
| Oneshot (World).zip | oneshot (14/14) |
| Orbs (World) (Erwin's Collection).zip | orbs (8/8) |
| Pacman (Canada) (Linux).zip | pacman (10/10) |
| Poizone (United Kingdom).zip | poizone (16/16) |
| Pulsar (World) (XBLIG).zip | pulsar (18/18) |
| Soccer (USA) (Proto).zip | soccer (21/21) |
| Solitaire (World) (Erwin's Collection).zip | solitaire (6/6) |
| Splatter (World).zip | splatterj (30/30) |
| StarHawk (World).zip | starhawk (9/9) |
| Super Pocket - The Data East Collection (World) (Extracted).zip | btime (15/15) |
| Super Pocket - The NeoGeo Collection (World) (Extracted).zip | mutnat (9/9) |
| Survival (World) (v1.6).zip | survival (14/14) |
| Thief (USA).zip | thief (12/12) |
| WolfPack (United Kingdom) (Disk 1).zip | wolfpack (11/11) |
| Zaxxon (Disk 1) (Unknown) (Side A).zip | zaxxon (17/17) |
| aligatun.zip | aligatorun (6/6) |
| berzerk1.zip | berzerkb (6/6) |
| bubbobr1.zip | bublboblr1 (18/18) |
| bubsympu.zip | bubsymphu (14/14) |
| buckyua.zip | buckyuab (13/13) |
| captavnu.zip | captavenu (21/21) |
| captcomu.zip | captcommu (15/15) |
| centtime.zip | centiped (6/6) |
| chplftb.zip | chopliftu (15/15) |
| commandu.zip | commandou (22/22) |
| crimfgt2.zip | crimfght (8/8) |
| ddragn2u.zip | ddragon2u (18/18) |
| defendg.zip | defenderg (12/12) |
| flicky.zip | flicky (12/12) |
| frogger.zip | frogger (9/9) |
| grdius3e.zip | gradius3 (25/25) |
| gunsmoku.zip | gunsmokeuc (32/32) |
| ikari3nr.zip | ikari3 (28/28) |
| joust.zip | joust (13/13) |
| landmkrp.zip | landmakrp (42/42) |
| mainev2p.zip | mainevt2p (11/11) |
| moonwlkb.zip | mwalkbl2 (23/23) |
| mooua.zip | moomesauab (12/12) |
| mystwaru.zip | mystwarru (16/16) |
| noboranb.zip | nobb (15/15) |
| punishru.zip | punisheru (22/22) |
| punksht2.zip | punkshot2 (8/8) |
| puyopuya.zip | puyoja (5/5) |
| puzloopu.zip | puzzloopu (7/7) |
| ramprt2p.zip | rampart2p (7/7) |
| robocp2u.zip | robocop2ua (25/25) |
| seganinu.zip | seganinju (15/15) |
| sf1us.zip | sf (44/44) |
| shangonb.zip | shangonrb (29/29) |
| sidearmr.zip | sidearmsur1 (27/27) |
| simpsn2p.zip | simpsons2p (13/13) |
| slammasu.zip | slammastu (28/28) |
| snowbrob.zip | snowbrosb (4/4) |
| spidey.zip | spidmanu (20/20) |
| ssrdrubc.zip | ssridersubc (10/10) |
| tapper.zip | tappera (19/19) |
| thndrbdj.zip | thndrbld1 (32/32) |
| tmnt22p.zip | tmnt22pu (12/12) |
| tnzsb.zip | tnzs (11/11) |
| vendet2p.zip | vendetta2pw (9/9) |
| xmen2p.zip | xmen2pa (12/12) |

## C. Sets arcade probables (revisar)

| ZIP | Candidatos | Cobertura |
|-----|-----------|-----------|
| 1944 (World) (Erwin's Collection).zip | 1944u (14/15), 1944ad (13/15) | 93% |
| Block (World).zip | blockbl (12/27), blockj (10/27) | 44% |
| Cameltry (Japan) (3.5 inch).zip | cameltrya (7/13), cameltry (7/13) | 54% |
| Cotton (Japan) (X68000).zip | cotton (30/64), cottonja (30/64) | 47% |
| DDragon (World) (v1.6.6).zip | ddragon6809 (29/111), ddragonm (29/111) | 26% |
| Defender (Europe).zip | defender (14/97), defenderg (13/97) | 14% |
| Dogfight (World) (v4.4.33).zip | dogfightp (12/19), dogfight (10/19) | 63% |
| Domino (Sweden) (En) (3.5 inch).zip | dominoa (14/18), domino (14/18) | 78% |
| Guzzler (Taiwan) (Othello Multivision) (Unl).zip | guzzlers (20/25), guzzler (15/25) | 80% |
| Hero (World).zip | hero (13/29), herodk (13/29) | 45% |
| Jungler (USA, Europe).zip | jungler (12/34), junglers (12/34) | 35% |
| Mosaic (World) (v0.32).zip | mosaica (10/11), mosaic (10/11) | 91% |
| Omega (USA).zip | omegaa (15/16), omega (15/16) | 94% |
| Peggle (World) (XBLA).zip | peggle (6/7), pegglet (6/7) | 86% |
| Pirates (World) (5858086C) (Addon).zip | pirates (11/14), piratesb (11/14) | 79% |
| Poitto (World) (Erwin's Collection).zip | poitto (8/9), poittoc (7/9) | 89% |
| Scramble (World).zip | spctrek (14/132), kamikazesp (14/132) | 11% |
| Skyfox (Disk 1) (Unknown) (Side A).zip | exerizerb (13/17), exerizer (13/17) | 76% |
| Super Pocket - The Atari Collection (World) (Extracted).zip | berzerk (8/35), berzerka (8/35) | 23% |
| Tokio (Japan) (PC-9801).zip | tokioo (26/33), tokio (26/33) | 79% |
| Turbo (USA).zip | turboe (38/65), turbob (38/65) | 58% |
| Turtles (Europe).zip | 600 (10/34), turpin (10/34) | 29% |
| Yamato (Japan, Europe, Australia, New Zealand) (En).zip | yamatou (16/22), yamatoa (15/22) | 73% |
| arknoidu.zip | arkanoidu (8/9), ark1balla (6/9) | 89% |
| dw.zip | dynwara (38/43), dynwarj (37/43) | 88% |
| gaunt2p.zip | gauntlet2p (16/17), gauntlet2pj (14/17) | 94% |
| qix.zip | qix2 (17/69), qixa (17/69) | 25% |
| sf2t.zip | sf2hfj (17/18), sf2hfjb2 (15/18) | 94% |
| vigilntu.zip | vigilantbl (15/17), vigilantg (8/17) | 88% |

## D. Romhacks / traducciones — plataforma por extensión interna

| ZIP | Plataforma |
|-----|-----------|
| Advanced Busterhawk Gleylancer (Japan) [T-En by M.I.J.E.T. v061023].zip | megadrive |
| Bio Miracle Baby Upa!! (Japan) [T-En by Vice Translations v1.00] [n].zip | nes |
| Captain Tsubasa Vol. II - Super Striker (Japan) [T-En by Hayabusakun v1.0].zip | nes |
| Chronicle of the Radia War (Japan) [T-En by Dreamless & Jair & [cx] v1.00] [n].zip | nes |
| Coca-Cola Kid (Japan) [T-En by Filler v1.1].zip | gamegear |
| Dahna - Goddess' Birth (Japan) [T-En by Cccmar v1.0] [n].zip | megadrive |
| Digital Devil Story - Megami Tensei (Japan) (FM77AV) (Disk 2).zip | nes |
| Downtown Special - Kunio-kun no Jidaigeki Dayo Zenin Shuugou! (J) [T Eng1.0_TechnosSamuraiTeam].zip | nes |
| Dragon Quest III - And into the Legend... (Japan) [T-En by DQ Translations v1.1] [n].zip | snes |
| Fairytale Dreams of Alice, The (Japan) [T-En by Dave Shadoff & Diogo Ribeiro & Filler & MooZ v1.0] [n].zip | pcengine |
| Fire Emblem - Mystery of the Emblem (Japan) [T-En by RPGuy96 & VincentASM v0.98] [Add by Quirino v0.14] [Add by RobertTheSable v0.22] [n].zip | snes |
| Fire Emblem - Shadow Dragon and the Blade of Light (Japan) [T-En by Polinym v1.2] [n].zip | nes |
| Fire Emblem - The Binding Blade (Japan) [T-En by Dark Twilkitri Net Translation Division v2.1] [Add by Gringe v1.1.3] [n].zip | gba |
| For the Frog the Bell Tolls (Japan) [T-En by Ryanbgstl v1.0] [n].zip | gb |
| Ganbare Goemon Gaiden - The Missing Golden Pipe (Japan) [T-En by Adventurous Translations v0.99c] [n].zip | nes |
| Ganbare Goemon Gaiden 2 - Treasures of the World (Japan) [T-En by Adventurous Translations v1.01] [n].zip | nes |
| Ganbare Goemon! (Japan) [T-En by Spinner 8 and friends v1.01] [n].zip | nes |
| Gen the Carpenter (Japan) (SGB Enhanced) (GB Compatible) [T-En by PentarouZero v1.0] [n].zip | gbc |
| Go Go! Nekketu Hockey Club - Multi-Sport Battle (Japan) [T-En by Disconnected Translations v0.99] [Add by GAFF Translations v1.00] [n].zip | nes |
| Go for it! Goemon - The Twinkling Journey - The Reason I became a Dancer (Japan) [T-En by DDSTranslation v3.0] [n].zip | snes |
| Go for it! Goemon 2 (Japan) [T-En by Stardust Crusaders v2.00] [n].zip | nes |
| Go for it! Goemon 2 - The Strange General McGuinness (Japan) [T-En by DDSTranslation v3.0] [n].zip | snes |
| Go for it! Goemon 3 - The Mecha Leg Hold of Jurokube Shishi (Japan) [T-En by DDSTranslation v4.0] [n].zip | snes |
| Hudson's Adventure Island IV (Japan) [T-En by Zynk Oxhyde v1.0] [n].zip | nes |
| Kaiketsu Yancha Maru 2 - Karakuri Land (Japan) [T-En by Derrick Sobodash v1.2].zip | nes |
| Kid Niki 3 (Japan) [T-En by Suicidal Translations v1.00] [Add by MottZilla v1.0] [Add by Proveaux v1.0] [n].zip | nes |
| King of Demons (Japan) [T-En by Aeon Genesis v1.01] [n].zip | snes |
| Legend of Fuma, The [Japan] [T-En by Nebulous Translations v1.01] [n].zip | nes |
| Mobile Suit Gundam Wing - Endless Duel (Japan) [T-En by Aeon Genesis v1.00] [n].zip | snes |
| Mysterious Dungeon 2 - Shiren the Wanderer (Japan) [T-En by Aeon Genesis v1.00] [n].zip | snes |
| Nadia - The Secret of Blue Water (Japan) [T-En by Eien Ni Hen & KingMike v1.1] [n].zip | megadrive |
| Nekketsu! Street Basket - Go for it, Dunk Heroes! (Japan) [T-En by Farid v1.2] [n].zip | nes |
| Perman - Return the Space Saucer! (Japan) [T-En by Zynk Oxhyde v2.0] [n].zip | nes |
| Perman 2 - Down with the Secret Madou Society! (Japan) [T-En by KingMike's Translations v1.0] [Add by FlashPV] [n].zip | nes |
| Pokemon Trading Card Game 2 - The Invasion of Team GR! (Japan) [T-En by Artemis251 & Jazz v1.0] [n].zip | gbc |
| Psy-O-Blade (Japan) (FM77AV) (Disk 1).zip | megadrive |
| Raging Fire - Recca (Japan) [T-En by Aeon Genesis v1.00] [n].zip | nes |
| Rhythm Heaven Silver (Japan) [T-En by W hat Beta 13a] [n].zip | gba |
| Royal Stone (Japan) [T-En by Aeon Genesis v1.00] [n].zip | gamegear |
| Samurai Pizza Cats (Japan) [T-En by Vice Translations v1.01] [US adaptation] [n].zip | nes |
| Shiren the Wanderer 2 - Oni Invasion! Shiren Castle! (Japan) [T-En by SharkSnack & Ozidual & KmbTos v1.02] [n].zip | n64 |
| Splatter House - Super Deformed (Japan) [T-En by Spinner 8 and friends v2.00] [n].zip | nes |
| Tactics Ogre - Let Us Cling Together (Japan) (Demo).zip | snes |
| Torneco no Daibouken - Fushigi no Dungeon (Japan) [T-En by Dynamic Designs v0.99].zip | snes |
| TwinBee 3 - The Aimless Demon King (Japan) [T-En by Demiforce & Stardust Crusaders v1.01] [n].zip | nes |
| Undead Line (Japan) (Mega Drive).zip | megadrive |
| Violinist of Hameln, The (Japan) [T-En by J2e Translations v1.00] [n].zip | snes |
| Wai Wai World (Japan) [T-En by Zynk Oxhyde v2.2] [n].zip | nes |
| Wai Wai World 2 - SOS!! Parsley Castle (Japan) [T-En by Vice Translations v1.01] [Add by Chronix v1.0] [n].zip | nes |

## E. Colecciones reales — extraer al Inbox

| ZIP | Entradas | Contenido |
|-----|----------|-----------|
| Arcade - Mame 2003 Plus.zip | 375 | .zip |
| Atari - 2600.zip | 50 | .zip |
| MAME BIOS 0.277.zip | 1465 | .zip |
| NEC - TurboGrafx CD.zip | 25 | .chd |
| NEC - TurboGrafx-16.zip | 80 | .zip |
| Nintendo - DS.zip | 100 | .zip |
| Nintendo - Game Boy Advance.zip | 150 | .zip |
| Nintendo - Game Boy Color.zip | 100 | .zip |
| Nintendo - Game Boy.zip | 150 | .zip |
| Nintendo - N64.zip | 100 | .zip |
| Nintendo - NES.zip | 275 | .zip |
| Nintendo - SNES.zip | 325 | .zip |
| SNK - NEO GEO.zip | 139 | .zip |
| Sega - Genesis (Update 1).zip | 25 | .zip |
| Sega - Genesis.zip | 150 | .zip |
| Sega - Sega CD.zip | 25 | .chd |

## F. Resto sin identificar (review manual)

| ZIP | Entradas | Extensiones |
|-----|----------|-------------|
| Digimon (World) (444D07E9) (Addon).zip | 2 | {'.bin': 1, '.svg': 1} |
