import json
import re
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
ASPCA_PATH = ROOT / "data" / "aspca_cats_plants.json"
CACHE_PATH = ROOT / "data" / "wikidata_zh_cache.json"
WIKIDATA_API = "https://www.wikidata.org/w/api.php"
WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"


MANUAL_ZH = {
    "Alocasia spp.": ("姑婆芋屬", ["海芋屬"]),
    "Aloe vera": ("蘆薈", ["庫拉索蘆薈"]),
    "Amaryllis spp.": ("孤挺花屬", ["朱頂紅屬"]),
    "Arum maculatum": ("斑葉疆南星", ["天南星"]),
    "Ricinus communis": ("蓖麻", []),
    "Chenopodium botrys": ("香藜", []),
    "Celastrus scandens": ("美洲南蛇藤", []),
    "Ilex opaca": ("美洲冬青", []),
    "Podophyllum peltatum": ("北美桃兒七", ["美洲鬼臼"]),
    "Taxus canadensus": ("加拿大紅豆杉", []),
    "Pieris japonica": ("馬醉木", ["日本馬醉木"]),
    "Aralia spinosa": ("刺楤木", []),
    "Malus sylvestrus": ("歐洲野蘋果", ["蘋果"]),
    "Prunus armeniaca": ("杏", ["杏樹"]),
    "Syngonium podophyllum": ("合果芋", []),
    "Zantedeschia aethiopica": ("海芋", ["馬蹄蓮"]),
    "Lilium asiatica": ("亞洲百合", []),
    "Asparagus densiflorus cv sprengeri": ("武竹", ["文竹"]),
    "Brassaia actinophylla": ("澳洲鴨腳木", ["昆士蘭傘木"]),
    "Colchicum autumnale": ("秋水仙", []),
    "Rhododendron spp": ("杜鵑花屬", ["杜鵑"]),
    "Cordyline terminalis": ("朱蕉", []),
    "Aloe barbadensis": ("庫拉索蘆薈", ["蘆薈"]),
    "Hippeastrum spp.": ("孤挺花屬", ["朱頂紅屬"]),
    "Caesalpinia pulcherrima": ("黃蝴蝶", ["金鳳花"]),
    "Poinciana gilliesii": ("黃蝴蝶", ["天堂鳥花"]),
    "Laurus nobilis": ("月桂", []),
    "Melia azedarach": ("苦楝", []),
    "Begonia spp.": ("秋海棠屬", []),
    "Citrus Aurantium": ("酸橙", []),
    "Strelitzia reginae": ("鶴望蘭", ["天堂鳥花"]),
    "Ammi majus": ("大阿米芹", []),
    "Apocynum androsaemifolium": ("夾竹桃麻", []),
    "Arum palestinum": ("巴勒斯坦疆南星", []),
    "Prunus serotina": ("黑櫻桃", []),
    "Solanum nigrum": ("龍葵", []),
    "Buxus spp.": ("黃楊屬", []),
    "Hedera helix": ("常春藤", ["西洋常春藤"]),
    "Coleus ampoinicus": ("到手香", ["左手香"]),
    "Brunfelsia species": ("鴛鴦茉莉屬", []),
    "Aesculus spp": ("七葉樹屬", []),
    "Fagopyrum spp.": ("蕎麥屬", []),
    "Podocarpus macrophylla": ("羅漢松", []),
    "Euonymus atropurpurea": ("美洲衛矛", []),
    "Ranunculus spp.": ("毛茛屬", []),
    "Iris spuria": ("假鳶尾", []),
    "Caladium hortulanum": ("彩葉芋", []),
    "Citrus mitis": ("四季橘", []),
    "Gardenia jasminoides": ("梔子花", []),
    "Carum carvi": ("葛縷子", []),
    "Zamia furfuracea": ("紙板蘇鐵", []),
    "Zamia spp.": ("澤米鐵屬", []),
    "Lobelia cardinalis": ("紅花半邊蓮", []),
    "Dianthus caryophyllus": ("康乃馨", []),
    "Nepeta cataria": ("貓薄荷", []),
    "Monstera deliciosa": ("龜背芋", ["蓬萊蕉"]),
    "Anthemis nobilis": ("羅馬洋甘菊", []),
    "Kalanchoe tubiflora": ("棒葉落地生根", []),
    "Dieffenbachia": ("黛粉葉屬", []),
    "Aglaonema modestum": ("廣東萬年青", []),
    "Crassula arborescens": ("銀葉景天", []),
    "Allium schoenoprasum": ("蝦夷蔥", []),
    "Prunus virginiana": ("弗吉尼亞稠李", []),
    "Helleborus niger": ("黑嚏根草", []),
    "Chrysanthemum spp.": ("菊屬", ["菊花"]),
    "Clematis spp.": ("鐵線蓮屬", []),
    "Gloriosa superba": ("嘉蘭", []),
    "Solanum dulcamara": ("歐白英", []),
    "Clivia spp.": ("君子蘭屬", []),
    "Dracaena spp.": ("龍血樹屬", []),
    "Lilium longiflorum": ("麝香百合", ["復活節百合"]),
    "Narcissus spp": ("水仙屬", []),
    "Dahlia species": ("大麗花屬", []),
    "Hemerocallis spp.": ("萱草屬", ["金針花屬"]),
    "Adenium obesum": ("沙漠玫瑰", []),
    "Epipremnum aureum": ("黃金葛", ["綠蘿", "魔鬼藤"]),
    "Chlorophytum comosum": ("吊蘭", ["蜘蛛草"]),
    "Nephrolepis exaltata": ("波士頓腎蕨", ["波士頓蕨"]),
    "Spathiphyllum": ("白鶴芋屬", ["白掌", "和平百合"]),
    "Sansevieria trifasciata": ("虎尾蘭", ["虎皮蘭"]),
    "Pachira aquatica": ("馬拉巴栗", ["發財樹"]),
    "Calathea spp.": ("竹芋屬", ["孔雀竹芋"]),
    "Crassula argentea": ("玉樹", ["翡翠木"]),
    "Lilium spp.": ("百合屬", ["百合"]),
    "Caesalpinia gilliesii": ("金鳳花", ["黃蝴蝶"]),
    "Caesalpinia gilliessi": ("金鳳花", ["黃蝴蝶"]),
    "Kalmia poliifolia": ("沼澤山月桂", []),
    "Borage officinalis": ("琉璃苣", []),
    "Borago officinalis": ("琉璃苣", []),
    "Clusia major": ("大葉書帶木", ["克魯西亞"]),
    "Acalypha godseffiana": ("紅邊鐵莧菜", []),
    "Philodendron oxycardium": ("心葉喜林芋", []),
    "Philodendron hederaceum": ("心葉喜林芋", []),
    "Philodendron bipennifolium": ("裂葉喜林芋", ["馬頭喜林芋"]),
    "Cycas and Zamia species": ("蘇鐵與澤米鐵類", []),
    "Cycas revoluta, zamia species": ("蘇鐵與澤米鐵類", ["蘇鐵"]),
    "Begonia scharfii": ("秋海棠屬植物", []),
    "Ambrosia mexicana": ("墨西哥豚草", []),
    "Anthurium scherzeranum": ("火鶴花", ["紅掌", "花燭"]),
    "Citrus paradisii": ("葡萄柚", []),
    "Giant Dracaena": ("巨龍血樹", ["龍血樹"]),
    "Hosta plataginea": ("玉簪", []),
    "Tradescantia flumeninsis": ("白花紫露草", ["水竹草"]),
    "Clivia minata": ("君子蘭", []),
    "Kalmia augustifolia": ("窄葉山月桂", []),
    "Kalmia latifolia": ("山月桂", []),
    "Lavendula angustifolia": ("薰衣草", ["真正薰衣草"]),
    "Lavandula angustifolia": ("薰衣草", ["真正薰衣草"]),
    "Citrus limonia": ("檸檬", []),
    "Aloysia triphylla": ("檸檬馬鞭草", []),
    "Citrus aurantifolia": ("萊姆", []),
    "Begonia cleopatra": ("克麗奧佩特拉秋海棠", []),
    "Begonia metallica": ("金屬葉秋海棠", []),
    "Phoradendron flavescens": ("美洲槲寄生", []),
    "Schefflera or Brassia actinoplylla": ("澳洲鴨腳木", ["傘樹"]),
    "Citrus sinensis": ("甜橙", ["柳橙"]),
    "Hemerocallis graminea": ("橙色萱草", []),
    "Origanum vulgare hirtum": ("希臘牛至", ["奧勒岡"]),
    "Begonia rex 'peace'": ("王秋海棠栽培品種", []),
    "Paeonis officinalis": ("芍藥", []),
    "Rheum rhabarbarium": ("食用大黃", ["大黃"]),
    "Begonia semperflorens cultivar": ("四季秋海棠栽培品種", []),
    "Cicuta maculata": ("斑毒芹", ["水毒芹"]),
    "Sphenosciadium capitellatum": ("白頭傘形花", []),
    "Lilium umbellatum": ("繖花百合", []),
    "Scindapsus pictus": ("銀斑葛", ["絲緞黃金葛"]),
    "Rumex scutatus": ("盾葉酸模", []),
    "Cymopterus watsonii": ("沃森春芹", []),
    "Lilium orientalis": ("東方百合", []),
    "tradescantia multiflora": ("多花紫露草", []),
    "Euonymus occidentalis": ("西美衛矛", []),
    "Prosopis limensis": ("利馬牧豆樹", []),
    "Pilea cadieri": ("冷水花", ["鋁葉草"]),
    "Antirrhinum multiflorum": ("多花金魚草", []),
    "Neoregalia spp.": ("彩葉鳳梨屬植物", ["姬鳳梨"]),
    "Eleagnus spp.": ("胡頹子屬植物", []),
    "Smilax laurifolia": ("月桂葉菝葜", []),
    "Cucurbita maxima var. banana": ("香蕉南瓜", []),
    "Cissus dicolor": ("雙色白粉藤", []),
    "Pellionia daveauana": ("蔓性赤車使者", []),
    "Carya laciniosa": ("大果山核桃", []),
    "Carya aquatica": ("水山核桃", []),
    "Crataegus douglasii": ("道格拉斯山楂", []),
    "Echeveria glauca": ("藍石蓮", []),
    "Dichelostemma pulchellum": ("美麗雙腺花", []),
    "Hookera pulchella": ("美麗雙腺花", []),
    "Brodiaea pulchella": ("美麗雙腺花", []),
    "Nephrolepis exalta bostoniensis": ("波士頓腎蕨", []),
    "Nolina tuberculata": ("酒瓶蘭", []),
    "Clintonia uniflora": ("單花七筋姑", []),
    "Smilax hispida": ("刺菝葜", []),
    "Sedum morganianum": ("玉綴", []),
    "Calathea insignis": ("響尾蛇竹芋", ["孔雀竹芋"]),
    "Maranta insignis": ("響尾蛇竹芋", []),
    "Plectranthus coleoides": ("香茶菜屬植物", []),
    "Hypocyrta nummularia": ("金魚花", []),
    "Dypsis lutescens, chrysalidocarpus lutescens (alternate scientific name)": ("散尾葵", ["黃椰子"]),
    "Canna generalis": ("美人蕉", []),
    "Gloxinia perennis": ("多年生落雪泥", []),
    "Jacaranda procera": ("藍花楹屬植物", []),
    "Tsuga caroliniana": ("卡羅萊納鐵杉", []),
    "Smilax herbacea": ("草本菝葜", []),
    "Stapelia hirsata": ("毛犀角", []),
    "Onychium japonica": ("日本金粉蕨", []),
    "Daucus carota var. sativa": ("胡蘿蔔", []),
    "Cattleya labiata": ("唇瓣嘉德麗雅蘭", []),
    "Celosia globosa": ("圓穗青葙", []),
    "Celosia plumosa": ("羽狀雞冠花", []),
    "Celosia spicata": ("穗狀青葙", []),
    "Anthericum comosum": ("吊蘭", []),
    "Chlorophytum bichetti": ("銀邊吊蘭", []),
    "Episcia dianthiflora": ("白花喜蔭花", []),
    "Polystichum acrostichoides": ("聖誕蕨", []),
    "Cattleya trianaei": ("特里亞納嘉德麗雅蘭", []),
    "Bulbophyllum appendiculatum": ("石豆蘭屬植物", []),
    "Pellaea rotundifolia": ("圓葉旱蕨", []),
    "Cattleya forbesii": ("福氏嘉德麗雅蘭", []),
    "Camellia japonica; Thea japonica": ("山茶", ["茶花"]),
    "Echeveria multicaulis": ("多莖擬石蓮花", []),
    "Asarina erubescens": ("蔓性金魚草", []),
    "Rubus pedatus": ("匍匐懸鉤子", []),
    "Aloe retusa": ("鈍葉蘆薈", []),
    "Davallia fejeensis": ("兔腳蕨", []),
    "Eriogonium inflatum": ("沙漠號角蓼", []),
    "Dichorisandra reginae": ("女王藍耳草", []),
    "Anethum graveolena": ("蒔蘿", []),
    "Dinteranthus vanzylii": ("番杏科多肉植物", []),
    "Nephrolepsis cordifolia 'duffii'": ("腎蕨栽培品種", []),
    "Nephrolepis exalta": ("腎蕨", []),
    "Cryptanthus bivattus minor": ("姬鳳梨", []),
    "Veitchia merillii": ("聖誕椰子", []),
    "Nephrolepsis cordifolia plumosa": ("腎蕨栽培品種", []),
    "Cattleya mossiae": ("莫氏嘉德麗雅蘭", []),
    "Townsendia sericea": ("絹毛湯森菊", []),
    "Rhapis flabelliformis": ("棕竹", []),
    "Ixora coccinea": ("龍船花", []),
    "Encyclia tampensis": ("佛羅里達蝴蝶蘭", []),
    "Epidendrum tampense": ("樹蘭屬植物", []),
    "Nephrolepsis exalta": ("腎蕨", []),
    "Polyrrhiza lindenii": ("鬼蘭", []),
    "Sedum weinbergii": ("朧月", []),
    "Ploystichum munitum": ("西部劍蕨", []),
    "Albiflora spp.": ("白花紫露草類", []),
    "Haemaria discolor": ("血葉蘭", ["寶石蘭"]),
    "Oncidium sphacelatum": ("文心蘭屬植物", []),
    "Muscari armeniacum": ("亞美尼亞葡萄風信子", []),
    "Cissus rhombifolia": ("菱葉白粉藤", []),
    "Hoya carnosa 'krinkle kurl'": ("毬蘭栽培品種", []),
    "Fuchsia triphylla": ("三葉倒掛金鐘", []),
    "Cucurbita maxima var. hubbard": ("哈伯德南瓜", []),
    "Lampranthus piquet": ("冰花屬多肉植物", []),
    "Peperomia griseoargentea": ("銀葉椒草", []),
    "Smilax lanceolata": ("披針葉菝葜", []),
    "Ixora javanica": ("爪哇龍船花", []),
    "Saintpaulia confusa": ("非洲紫羅蘭", []),
    "Anoectuchilus setaceus": ("金線蓮屬植物", []),
    "Fuschsia spp.": ("倒掛金鐘屬植物", []),
    "Rhapis flabelliformus": ("棕竹", []),
    "Draceana spp.": ("龍血樹屬植物", []),
    "Peperomia crassifolia": ("厚葉椒草", []),
    "Dendrobium gracilicaule": ("石斛蘭屬植物", []),
    "Odontoglossum pulchellum": ("齒舌蘭屬植物", []),
    "Haworthia subfasciata": ("十二之卷", []),
    "Lithops naureeniae": ("生石花", []),
    "Veitchia merrillii": ("聖誕椰子", []),
    "Calochortus gunnisonii": ("岡尼森山百合", []),
    "Echeveria derenbergii": ("靜夜", []),
    "Acantha": ("網紋草類植物", []),
    "Echeveria Pulinata": ("絨毛石蓮花", []),
    "Echevaria": ("擬石蓮花屬植物", []),
    "Phoenix robellinii": ("矮海棗", []),
    "Calathea micans": ("竹芋屬植物", []),
    "Rhipsalis cassutha": ("絲葦", []),
    "Carya tomentosa": ("硬殼山核桃", []),
    "Bertolonia mosaica": ("錦葉草屬植物", []),
    "Silene acaulis": ("無莖蠅子草", []),
    "Secum weinbergii": ("朧月", []),
    "Guzmania lingulata minor": ("小舌穗花鳳梨", []),
    "Soleirolia soleirolii": ("嬰兒淚", []),
    "Miltonia roezlii alba": ("米爾頓蘭屬植物", []),
    "Haworthia margaritifera": ("珍珠瓦葦", []),
    "Peperomia peltifolia": ("盾葉椒草", []),
    "Peperomia rotundifolia": ("圓葉椒草", []),
    "Tolmeia menziesii": ("托梅亞草", []),
    "Carya glabra": ("光皮山核桃", []),
    "Leucospermum incisum": ("針墊花", []),
    "Episcia cultivar": ("喜蔭花栽培品種", []),
    "Plantanus occidentalis": ("美國梧桐", []),
    "Ceratostigma larpentiae": ("藍雪花屬植物", []),
    "Echeveria pul-oliver": ("擬石蓮花屬植物", []),
    "Zephyranthes drummondii": ("蔥蘭屬植物", []),
    "Plectranthus oetendahlii": ("香茶菜屬植物", []),
    "Frithia pulchra": ("仙女象足", []),
    "Gynura aurantica": ("紫絨三七", []),
    "Hemigraphis exotica": ("紫背草", []),
    "Smilax walteria": ("沃氏菝葜", []),
    "Peperomia clusiifolia": ("紅邊椒草", []),
    "Cordyline rubra": ("紅朱蕉", []),
    "elaeagnus species": ("胡頹子屬植物", []),
    "Poterium sanguisorba": ("地榆", []),
    "Leucocrinum montanum": ("山星百合", []),
    "Pellonia pulchra": ("美麗赤車使者", []),
    "Smilax glauca": ("粉背菝葜", []),
    "Vallota speciosa": ("君子蘭類植物", []),
    "Cryptanthus lacerdae": ("姬鳳梨屬植物", []),
    "NONE LISTED": ("銀樹", []),
    "Clintonia umbelluata": ("繖花七筋姑", []),
    "Epidendrum atropurpeum": ("樹蘭屬植物", []),
    "Cleome hasserlana": ("醉蝶花", []),
    "Sorghum vulgare var sudanesis": ("蘇丹草", []),
    "Eriogonium umbellatum": ("繖花蕎麥蓼", []),
    "helianthus angustifolius": ("沼澤向日葵", []),
    "Plectranthus australis": ("瑞典常春藤", []),
    "Mammillaria fragilis": ("乳突球屬仙人掌", []),
    "Coreopsis californica": ("加州金雞菊", []),
    "Peperomia prostata": ("蔓性椒草", []),
    "Kohleria lindeniana": ("苦苣苔科植物", []),
    "Santpaulia confusa": ("非洲紫羅蘭", []),
    "Peperomia serpens variegata": ("斑葉蔓性椒草", []),
    "Echeveria gilva": ("吉娃蓮類擬石蓮花", []),
    "Anthirrhinum multiflorum": ("多花金魚草", []),
    "Cucurbia pepo cv zucchini": ("櫛瓜", []),
    "Scindapsus, Philodendron spp": ("斑葉喜林芋", ["斑葉藤芋"]),
    "Hoya publcalyx": ("銀粉毬蘭", ["粉斑毬蘭"]),
    "Epidendrum prismatocarpum": ("彩虹樹蘭", []),
}

GENUS_ZH = {
    "Acalypha": "鐵莧菜屬",
    "Aloe": "蘆薈屬",
    "Ambrosia": "豚草屬",
    "Anthurium": "花燭屬",
    "Begonia": "秋海棠屬",
    "Calathea": "竹芋屬",
    "Carya": "山核桃屬",
    "Cattleya": "嘉德麗雅蘭屬",
    "Citrus": "柑橘屬",
    "Clintonia": "七筋姑屬",
    "Cryptanthus": "姬鳳梨屬",
    "Echeveria": "擬石蓮花屬",
    "Echevaria": "擬石蓮花屬",
    "Epidendrum": "樹蘭屬",
    "Eriogonium": "蕎麥蓼屬",
    "Haworthia": "瓦葦屬",
    "Hoya": "毬蘭屬",
    "Hypocyrta": "金魚花屬",
    "Ixora": "龍船花屬",
    "Lilium": "百合屬",
    "Neoregalia": "彩葉鳳梨屬",
    "Peperomia": "椒草屬",
    "Philodendron": "喜林芋屬",
    "Plectranthus": "香茶菜屬",
    "Smilax": "菝葜屬",
    "Tradescantia": "紫露草屬",
}


def load_json(path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def clean_scientific_name(value):
    value = re.sub(r"\s+", " ", value or "").strip()
    value = re.sub(r"\s+(spp?\.?|species|sp\.)$", "", value, flags=re.I)
    value = re.sub(r"\s+cv\s+.+$", "", value, flags=re.I)
    return value.strip()


def request_json(params):
    url = f"{WIKIDATA_API}?{urlencode(params)}"
    request = Request(url, headers={"User-Agent": "catna-data-enricher/1.0"})
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def request_sparql(query):
    url = f"{WIKIDATA_SPARQL}?{urlencode({'query': query, 'format': 'json'})}"
    request = Request(url, headers={"User-Agent": "catna-data-enricher/1.0"})
    with urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def sparql_string(value):
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def wikidata_batch_taxon_lookup(names):
    names = [name for name in names if name]
    if not names:
        return {}

    values = " ".join(sparql_string(name) for name in names)
    query = f"""
SELECT ?taxonName ?taxon ?taxonLabel ?altLabel WHERE {{
  VALUES ?taxonName {{ {values} }}
  ?taxon wdt:P225 ?taxonName.
  SERVICE wikibase:label {{
    bd:serviceParam wikibase:language "zh-tw,zh-hant,zh,en".
    ?taxon rdfs:label ?taxonLabel.
  }}
  OPTIONAL {{
    ?taxon skos:altLabel ?altLabel.
    FILTER(LANG(?altLabel) IN ("zh", "zh-tw", "zh-hant"))
  }}
}}
"""
    data = request_sparql(query)
    results = {}
    for row in data.get("results", {}).get("bindings", []):
        name = row.get("taxonName", {}).get("value", "")
        label = row.get("taxonLabel", {}).get("value", "")
        alias = row.get("altLabel", {}).get("value", "")
        qid = row.get("taxon", {}).get("value", "").rsplit("/", 1)[-1]
        if not name or not label or not any(chinese_char(char) for char in label):
            continue
        item = results.setdefault(name, {"label": label, "aliases": [], "qid": qid})
        if alias and alias != label and alias not in item["aliases"]:
            item["aliases"].append(alias)
    return results


def wikidata_search(query):
    if not query:
        return None
    data = request_json(
        {
            "action": "wbsearchentities",
            "format": "json",
            "language": "en",
            "uselang": "zh-tw",
            "search": query,
            "limit": "5",
        }
    )
    for item in data.get("search", []):
        label = item.get("label", "")
        description = item.get("description", "")
        if label and any(chinese_char(char) for char in label):
            aliases = [
                alias
                for alias in item.get("aliases", [])
                if any(chinese_char(char) for char in alias)
            ]
            return {"label": label, "aliases": aliases, "qid": item.get("id"), "description": description}
    return None


def chinese_char(char):
    return "\u4e00" <= char <= "\u9fff"


def translation_for(plant, cache):
    scientific = plant.get("scientific_name", "")
    if scientific in MANUAL_ZH:
        label, aliases = MANUAL_ZH[scientific]
        return label, aliases, "manual"

    cleaned = clean_scientific_name(scientific)
    for key in [scientific, cleaned, plant.get("common_name_en", "")]:
        if not key:
            continue
        if key not in cache:
            continue
        item = cache[key]
        if item and item.get("label"):
            aliases = [alias for alias in item.get("aliases", []) if alias != item["label"]]
            return item["label"], aliases[:8], "wikidata"

    return "", [], ""


def generated_translation_for(plant):
    scientific = clean_scientific_name(plant.get("scientific_name", ""))
    common = plant.get("common_name_en", "")

    if not scientific and common == "Medicine Plant":
        return "蘆薈", ["藥用蘆薈"]

    genus = scientific.split(" ", 1)[0] if scientific else ""
    genus = genus[:1].upper() + genus[1:] if genus else ""
    if genus in GENUS_ZH:
        return f"{GENUS_ZH[genus]}植物", []

    if common:
        return f"{common}（暫無正式中文名）", []

    return "暫無正式中文名植物", []


def main():
    aspca_data = load_json(ASPCA_PATH, {})
    cache = load_json(CACHE_PATH, {})
    plants = aspca_data.get("plants", [])

    candidate_names = sorted(
        {
            clean_scientific_name(plant.get("scientific_name", ""))
            for plant in plants
            if plant.get("scientific_name") and plant.get("scientific_name") not in MANUAL_ZH
        }
    )
    missing = [name for name in candidate_names if name and name not in cache]
    for index in range(0, len(missing), 60):
        batch = missing[index : index + 60]
        try:
            cache.update(wikidata_batch_taxon_lookup(batch))
            for name in batch:
                cache.setdefault(name, None)
            save_json(CACHE_PATH, cache)
            time.sleep(1.2)
        except Exception as exc:
            print(f"batch failed at {index}: {exc}")
            save_json(CACHE_PATH, cache)
            time.sleep(8)

    for plant in plants:
        label, aliases, source = translation_for(plant, cache)
        if not label:
            label, aliases = generated_translation_for(plant)
            source = "generated"
        plant["common_name_zh"] = label
        plant["aliases_zh"] = aliases
        plant["zh_source"] = source
        if plant.get("id") == "aspca-catnip":
            plant["cat_toxicity"] = "safe"
            plant["catToxicityNote"] = (
                "本系統依植物本身成分毒性判定為低風險；ASPCA 詳細頁提醒大量食用可能造成嘔吐或腹瀉，"
                "但這類腸胃反應不作為本系統的有毒分類依據。"
            )
            plant["symptoms"] = "未列出特定毒性症狀。"

    aspca_data.setdefault("metadata", {})["zh_enriched"] = True
    aspca_data["metadata"]["zh_translation_note"] = (
        "Chinese labels come from local manual overrides, Wikidata search results, "
        "and generated fallback labels for records without a reliable Chinese name. "
        "Generated labels should be reviewed for horticultural naming accuracy."
    )

    save_json(ASPCA_PATH, aspca_data)
    save_json(CACHE_PATH, cache)

    translated = sum(1 for plant in plants if plant.get("common_name_zh"))
    manual = sum(1 for plant in plants if plant.get("zh_source") == "manual")
    wikidata = sum(1 for plant in plants if plant.get("zh_source") == "wikidata")
    print(f"translated={translated}/{len(plants)}")
    print(f"manual={manual}, wikidata={wikidata}, untranslated={len(plants) - translated}")


if __name__ == "__main__":
    main()
