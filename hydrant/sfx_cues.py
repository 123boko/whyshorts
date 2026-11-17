# Sound design for "Why Does the Fire Hydrant on Your Street Never Freeze?"
def cues(w, wend, B):
    ev = []
    for t in [B(2), B(3), w('run') - 0.3, B(5) + 0.1, w('closed') - 0.3, w('nut') - 0.5, w('tiny') - 0.4, B(9) - 0.1, B(10) - 0.1, B(11) - 0.05]:
        ev.append(('whoosh', t - 0.15, -14))
    for t in [w('january'), w('nine'), w('main'), w('line'), w('never'), w('freezing'), w('firefighters'), w('pipe', 3), w('block'), w('move'),
              w('seven'), w('empty'), w('dry'), w('rod'), w('nut'), w('still'), w('drain'), w('gravel'), B(9), w('florida'), w('wet')]:
        ev.append(('pop', t - 0.05, -16))
    ev += [('freeze', w('freezes') - 0.1, -9), ('crack', w('cracks') - 0.05, -4), ('freeze', w('freezes', 3) - 0.05, -8),
           ('fill', w('full', 2) - 0.6, -10), ('fill', w('opens') + 0.1, -9), ('fill', w('stay') - 0.4, -11),
           ('clunk', w('move') + 1.35, -8), ('wrench', w('turn') - 0.1, -7), ('wrench', w('turn') + 0.6, -9),
           ('gush', w('shoots') - 0.3, -7), ('clunk', w('shut') - 0.1, -10),
           ('drain', w('opens', 2), -4), ('drain', w('opens', 2) + 1.0, -5), ('drain', w('opens', 2) + 2.0, -7),
           ('fire', w('fire') - 0.4, -10), ('fire', w('fire') + 1.5, -12)]
    beds = [('wind', 0.0, B(10), -26), ('birds', B(10), 64.3, -22)]
    return ev, beds
