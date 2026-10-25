"""Small, static teaching diagrams for the listening guide. No audio rendering."""

from html import escape
from pathlib import Path

COLORS = ("#2363d1", "#b65a13", "#8451b2", "#14735b")
INK, MUTED, PAPER = "#203047", "#59687a", "#fbfaf6"


def text(x, y, words, size=20, color=INK, weight=400):
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" '
            f'font-weight="{weight}">{escape(words)}</text>')


def box(x, y, w, h, fill, radius=10, stroke="none"):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}"/>'


def line(x1, y1, x2, y2, color=MUTED, dashed=False):
    dash = ' stroke-dasharray="5 5"' if dashed else ''
    return f'<path d="M{x1} {y1} L{x2} {y2}" fill="none" stroke="{color}" stroke-width="2"{dash}/>'


def arrow(x1, y, x2):
    return line(x1, y, x2, y) + f'<path d="M{x2-8} {y-5} l8 5 l-8 5" fill="none" stroke="{MUTED}" stroke-width="2"/>'


def wave(x, y, width=140, periods=4, color=INK):
    half = width / (periods*2)
    points = [(x, y+12)]
    for i in range(periods*2):
        level = y-12 if i % 2 == 0 else y+12
        points += [(x+i*half, level), (x+(i+1)*half, level)]
    return '<polyline points="'+' '.join(f'{a},{b}' for a,b in points)+f'" fill="none" stroke="{color}" stroke-width="3"/>'


def speaker(x, y):
    return (f'<path d="M{x} {y+16} h18 l25 -20 v62 l-25 -20 h-18 Z" fill="{INK}"/>'
            f'<path d="M{x+54} {y+6} Q{x+78} {y+28} {x+54} {y+50}" fill="none" stroke="{INK}" stroke-width="4"/>')


def svg(title, content, height=540):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="{height}" '
            f'viewBox="0 0 1000 {height}" role="img" aria-labelledby="title desc">'
            f'<title id="title">{escape(title)}</title><desc id="desc">{escape(title)}. '
            'Blue is the melody; orange, purple and green are the three chord notes.</desc>'
            '<g font-family="Segoe UI, Arial, sans-serif">'+box(0,0,1000,height,PAPER,16)
            + ''.join(content)+'</g></svg>')


def header(label, title, subtitle):
    return [text(36,35,label,14,MUTED,700),text(36,76,title,30,INK,700),text(36,109,subtitle,19)]


def voices():
    out = []
    for i, label in enumerate(("M  Melody", "1   C", "2   E", "3   G")):
        y=137+i*40
        out += [box(36,y,146,32,COLORS[i],7),text(49,y+23,label,18,"white",600)]
    out += [text(36,316,"1 + 2 + 3 = chord",16,MUTED)]
    return out


def single_machine(caption):
    out=voices()
    for i in range(4):
        out.append(line(185,153+i*40,276,211))
    out += [box(276,145,280,146,"#eef2f7",14,"#cbd4df"),
            text(297,177,"ONE GENERATOR",16,MUTED,700),wave(308,211,210,5),
            text(297,270,caption,18),arrow(571,214,651),speaker(669,188),
            text(782,199,"One note",23,INK,700),text(782,229,"at a time",23),
            text(782,260,"The others wait.",16,MUTED)]
    return out


def strip(sequence, y=390):
    """A simplified turn-taking strip, read left to right."""
    out=[]
    x=36.
    total=sum(length for _,length in sequence)
    for voice,length in sequence:
        w=928*length/total
        out.append(box(x,y,w-2,44,COLORS[voice],3))
        if w>26:
            out.append(text(x+w/2-6,y+29,"M" if voice==0 else str(voice),18,"white",700))
        x+=w
    out += [text(36,y+68,"earlier",15,MUTED),arrow(102,y+63,882),text(898,y+68,"later",15,MUTED)]
    return out


def four_parts():
    out=header("MEET THE PLAYERS","One tune. Three notes underneath.","We use the same melody and chords in every experiment.")
    out += [box(36,139,435,170,"#eaf0fd"),text(58,174,"THE MELODY",16,COLORS[0],700),
            text(58,204,"The part you can hum",20),text(490,235,"+",32),
            box(530,139,434,170,"#f0ece5"),text(552,174,"THE CHORD",16,INK,700),
            text(552,204,"Three notes: C + E + G",20)]
    for i,note in enumerate(("E","E","F","G")):
        x=58+i*96
        out += [box(x,225,78,60,COLORS[0]),text(x+26,266,note,30,"white",700)]
    for i,note in enumerate(("C","E","G")):
        x=552+i*130
        out += [box(x,225,110,60,COLORS[i+1]),text(x+43,266,note,30,"white",700)]
    out += [text(36,355,"Four parts, but how many generators?",25,INK,700),
            text(36,392,"With one generator, the players take turns. With four, everyone can play together.",20),
            text(36,441,"The tune starts on E. The chord also contains E; these are still two separate parts.",18,MUTED)]
    return svg("Meet the four musical parts",out,480)


def together(version):
    out=header("FOUR VOICES / PLAYING TOGETHER", "Everyone gets a generator", 
               "Add the melody and three chord notes. Nobody has to wait.")
    out+=voices()
    for i in range(4):
        y=137+i*40
        out += [arrow(190,y+16,234),box(246,y,208,32,"#edf1f5",6),wave(262,y+16,170,(5,4,5,6)[i],COLORS[i]),
                line(464,y+16,526,213,COLORS[i])]
    out += [box(526,170,92,86,INK),text(550,220,"+",44,"white"),arrow(632,213,676),speaker(694,187),
            text(803,209,"All four",22,INK,700),text(803,238,"at once",22)]
    for i in range(4):
        out += [text(36,367+i*27,"M" if i==0 else str(i),17,COLORS[i],700),
                box(72,351+i*27,892,18,COLORS[i] if i==0 or version=="chords" else ("#f0c59f","#d8c3e9","#b1d6c8")[i-1],4)]
    out.append(text(36,503,"CHORDS: loud and plain." if version=="chords" else "SUMMED: same idea, with a quieter chord behind the tune.",20,INK,600))
    return svg(f"{version}: four independent square-wave generators",out)


def space():
    out=header("START HERE / SPACE","A little room around the music","Melody + soft chords + low bass, with echoes on the left and right.")
    out+=voices()
    for i in range(4):
        out.append(line(189,153+i*40,287,211,COLORS[i]))
    out += [box(287,145,270,145,"#edf1f5"),text(309,181,"Softer instruments",23,INK,700),
            text(309,218,"A retro lead",20),text(309,251,"and a gentle backing",20),arrow(572,212,643),
            speaker(674,174),text(782,201,"Left + right",23,INK,700),
            text(782,233,"Small echoes",20),text(782,263,"A wider sound",18,MUTED)]
    out += [text(36,362,"A note...",19,INK,600),text(409,362,"...comes back a little quieter.",19),
            box(36,386,218,45,COLORS[0]),box(293,386,170,45,"#789ee0"),
            box(502,386,132,45,"#a5bde7"),box(673,386,96,45,"#ccd9ee"),
            box(808,386,62,45,"#e0e8f4"),
            text(36,493,"More than square waves: this arrangement adds soft tones, bass and stereo effects.",19)]
    return svg("Space: softer instruments with stereo echoes",out)


def turns(version):
    data={
        "switch":("A very fast game of turns","Tune, chord note, tune, next chord note. Repeat.","Regular turns", "Equal turns: half the time for melody, half for the chord."),
        "less-chord":("Let the melody stay longer","Keep the order, but make the chord notes' turns shorter.","More melody time", "Three quarters melody. One quarter shared by the three chord notes."),
        "full-cycles":("Finish the wave before changing notes","Wait for a complete high + low pair, then choose the next note.","Whole waves only", "Switch here: at the start of the next complete wave."),
        "random":("Who goes next? Draw a name.","Choose a part after every complete wave. The tune gets most of the time.","One wave per draw", "No repeating order, but lots of tiny changes can sound rough."),
        "packets":("Give each note time to settle","Draw a part, keep it for 4-12 complete waves, then draw again.","4-12 waves per draw", "Longer turns make individual notes easier to hear."),
    }
    title,subtitle,caption,footer=data[version]
    out=header("ONE GENERATOR / TAKING TURNS",title,subtitle)+single_machine(caption)
    if version=="full-cycles":
        out += [text(36,358,"Complete waves",18,COLORS[0],700),text(561,358,"Next note: a different length",18,COLORS[1],700),
                wave(40,400,420,3,COLORS[0]),wave(460,400,480,2,COLORS[1]),
                line(460,363,460,441,INK,True),text(440,467,"change",16)]
    else:
        if version=="switch":
            sequence=[(i,1) for i in [0,1,0,2,0,3]*3]
        elif version=="less-chord":
            sequence=[(i,w) for c in [1,2,3]*2 for i,w in [(0,3),(c,1)]]
        elif version=="random":
            sequence=[(i,1) for i in [0,2,0,0,1,0,3,0,0,2,0,1,0,0,0,3,0,1,0,0,2,0,0,0,1,0,0,3]]
        else:
            sequence=[(0,9),(1,4),(0,8),(3,5),(0,12),(2,6),(0,10)]
        strip_label = ("Each small tick is a wave; each colored group is one turn." if version=="packets"
                       else "One strip = the one generator's playing time")
        out += [text(36,363,strip_label,18,MUTED)]+strip(sequence)
        if version=="packets":
            # Faint separators make the cycles within each packet visible.
            unit=928/sum(n for _,n in sequence)
            for i in range(1,sum(n for _,n in sequence)):
                out.append(line(36+i*unit,425,36+i*unit,433,PAPER))
    out.append(text(36,511,footer,19,INK,600))
    return svg(title,out)


def build_illustrations(directory):
    directory=Path(directory)
    directory.mkdir(exist_ok=True)
    images={"four_parts":four_parts(),"space":space(),"chords":together("chords"),"summed":together("summed")}
    images.update({name:turns(name) for name in ("switch","less-chord","full-cycles","random","packets")})
    for name,content in images.items():
        (directory/f"{name}.svg").write_text(content,encoding="utf-8")


if __name__=="__main__":
    build_illustrations(Path(__file__).resolve().parents[1]/"docs")
