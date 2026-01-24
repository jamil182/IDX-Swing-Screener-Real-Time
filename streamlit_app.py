import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_ta as ta
import requests
from datetime import datetime

# --- CONFIG ---
st.set_page_config(page_title="IDX Pro Screener 2026", layout="wide", page_icon="📈")

def send_telegram_msg(message):
    try:
        token = st.secrets["TELEGRAM_BOT_TOKEN"]
        chat_id = st.secrets["TELEGRAM_CHAT_ID"]
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        st.error(f"Gagal kirim Telegram: {e}")

# --- UI HEADER ---
st.title("🚀 IDX Swing Pro v2026")
st.markdown("Screener otomatis dengan **Risk & Money Management**.")

# --- SIDEBAR ---
st.sidebar.header("🔧 Parameter Filter")
rsi_min = st.sidebar.slider("Min RSI (14)", 0, 100, 45) # Lebih longgar agar hasil muncul
vol_ratio_min = st.sidebar.slider("Min Vol Ratio", 0.0, 5.0, 1.0, 0.1)
mcap_min = st.sidebar.number_input("Min Market Cap (Triliun)", 0.0, 1000.0, 0.5)
pct_1m_min = st.sidebar.slider("Min % 1 Bulan", -20, 100, 0)

st.sidebar.divider()
st.sidebar.header("💰 Money Management")
total_budget = st.sidebar.number_input("Total Modal (Rp)", value=10000000)
risk_per_trade = st.sidebar.slider("Resiko per Trade (%)", 0.1, 5.0, 1.0)
use_telegram = st.sidebar.toggle("Kirim ke Telegram", value=False)

# List Saham Anda (800+)
default_stocks = ["AADI.JK", "AALI.JK", "ABBA.JK", "ABDA.JK", "ABMM.JK", "ACES.JK", "ACRO.JK", "ACST.JK", "ADCP.JK", "ADES.JK", "ADHI.JK", "ADMF.JK", "ADMG.JK", "ADMR.JK", "ADRO.JK", "AEGS.JK", "AGAR.JK", "AGII.JK", "AGRO.JK", "AGRS.JK", "AHAP.JK", "AIMS.JK", "AISA.JK", "AKKU.JK", "AKPI.JK", "AKRA.JK", "AKSI.JK", "ALDO.JK", "ALII.JK", "ALKA.JK", "ALMI.JK", "ALTO.JK", "AMAG.JK", "AMAN.JK", "AMAR.JK", "AMFG.JK", "AMIN.JK", "AMMN.JK", "AMMS.JK", "AMOR.JK", "AMRT.JK", "ANDI.JK", "ANJT.JK", "ANTM.JK", "APEX.JK", "APIC.JK", "APII.JK", "APLI.JK", "APLN.JK", "ARCI.JK", "AREA.JK", "ARGO.JK", "ARII.JK", "ARKA.JK", "ARKO.JK", "ARMY.JK", "ARNA.JK", "ARTA.JK", "ARTI.JK", "ARTO.JK", "ASBI.JK", "ASDM.JK", "ASGR.JK", "ASHA.JK", "ASII.JK", "ASJT.JK", "ASLC.JK", "ASLI.JK", "ASMI.JK", "ASPI.JK", "ASPR.JK", "ASRI.JK", "ASRM.JK", "ASSA.JK", "ATAP.JK", "ATIC.JK", "ATLA.JK", "AUTO.JK", "AVIA.JK", "AWAN.JK", "AXIO.JK", "AYAM.JK", "AYLS.JK", "BABP.JK", "BABY.JK", "BACA.JK", "BAIK.JK", "BAJA.JK", "BALI.JK", "BANK.JK", "BAPA.JK", "BAPI.JK", "BATA.JK", "BATR.JK", "BAUT.JK", "BAYU.JK", "BBCA.JK", "BBHI.JK", "BBKP.JK", "BBLD.JK", "BBMD.JK", "BBNI.JK", "BBRI.JK", "BBRM.JK", "BBSI.JK", "BBSS.JK", "BBTN.JK", "BBYB.JK", "BCAP.JK", "BCIC.JK", "BCIP.JK", "BDKR.JK", "BDMN.JK", "BEBS.JK", "BEEF.JK", "BEER.JK", "BEKS.JK", "BELI.JK", "BELL.JK", "BESS.JK", "BEST.JK", "BFIN.JK", "BGTG.JK", "BHAT.JK", "BHIT.JK", "BIKA.JK", "BIKE.JK", "BIMA.JK", "BINA.JK", "BINO.JK", "BIPI.JK", "BIPP.JK", "BIRD.JK", "BISI.JK", "BJBR.JK", "BJTM.JK", "BKDP.JK", "BKSL.JK", "BKSW.JK", "BLES.JK", "BLOG.JK", "BLTA.JK", "BLTZ.JK", "BLUE.JK", "BMAS.JK", "BMBL.JK", "BMHS.JK", "BMRI.JK", "BMSR.JK", "BMTR.JK", "BNBA.JK", "BNBR.JK", "BNGA.JK", "BNII.JK", "BNLI.JK", "BOAT.JK", "BOBA.JK", "BOGA.JK", "BOLA.JK", "BOLT.JK", "BOSS.JK", "BPFI.JK", "BPII.JK", "BPTR.JK", "BRAM.JK", "BREN.JK", "BRIS.JK", "BRMS.JK", "BRNA.JK", "BRPT.JK", "BRRC.JK", "BSBK.JK", "BSDE.JK", "BSIM.JK", "BSML.JK", "BSSR.JK", "BSWD.JK", "BTEK.JK", "BTEL.JK", "BTON.JK", "BTPN.JK", "BTPS.JK", "BUAH.JK", "BUDI.JK", "BUKA.JK", "BUKK.JK", "BULL.JK", "BUMI.JK", "BUVA.JK", "BVIC.JK", "BWPT.JK", "BYAN.JK", "CAKK.JK", "CAMP.JK", "CANI.JK", "CARE.JK", "CARS.JK", "CASA.JK", "CASH.JK", "CASS.JK", "CBDK.JK", "CBMF.JK", "CBPE.JK", "CBRE.JK", "CBUT.JK", "CCSI.JK", "CDIA.JK", "CEKA.JK", "CENT.JK", "CFIN.JK", "CGAS.JK", "CHEK.JK", "CHEM.JK", "CHIP.JK", "CINT.JK", "CITA.JK", "CITY.JK", "CLAY.JK", "CLEO.JK", "CLPI.JK", "CMNP.JK", "CMNT.JK", "CMPP.JK", "CMRY.JK", "CNKO.JK", "CNMA.JK", "CNTB.JK", "CNTX.JK", "COAL.JK", "COCO.JK", "COIN.JK", "COWL.JK", "CPIN.JK", "CPRI.JK", "CPRO.JK", "CRAB.JK", "CRSN.JK", "CSAP.JK", "CSIS.JK", "CSMI.JK", "CSRA.JK", "CTBN.JK", "CTRA.JK", "CTTH.JK", "CUAN.JK", "CYBR.JK", "DAAZ.JK", "DADA.JK", "DART.JK", "DATA.JK", "DAYA.JK", "DCII.JK", "DEAL.JK", "DEFI.JK", "DEPO.JK", "DEWA.JK", "DEWI.JK", "DFAM.JK", "DGIK.JK", "DGNS.JK", "DGWG.JK", "DIGI.JK", "DILD.JK", "DIVA.JK", "DKFT.JK", "DKHH.JK", "DLTA.JK", "DMAS.JK", "DMMX.JK", "DMND.JK", "DNAR.JK", "DNET.JK", "DOID.JK", "DOOH.JK", "DOSS.JK", "DPNS.JK", "DPUM.JK", "DRMA.JK", "DSFI.JK", "DSNG.JK", "DSSA.JK", "DUCK.JK", "DUTI.JK", "DVLA.JK", "DWGL.JK", "DYAN.JK", "EAST.JK", "ECII.JK", "EDGE.JK", "EKAD.JK", "ELIT.JK", "ELPI.JK", "ELSA.JK", "ELTY.JK", "EMAS.JK", "EMDE.JK", "EMTK.JK", "ENAK.JK", "ENRG.JK", "ENVY.JK", "ENZO.JK", "EPAC.JK", "EPMT.JK", "ERAA.JK", "ERAL.JK", "ERTX.JK", "ESIP.JK", "ESSA.JK", "ESTA.JK", "ESTI.JK", "ETWA.JK", "EURO.JK", "EXCL.JK", "FAPA.JK", "FAST.JK", "FASW.JK", "FILM.JK", "FIMP.JK", "FIRE.JK", "FISH.JK", "FITT.JK", "FLMC.JK", "FMII.JK", "FOLK.JK", "FOOD.JK", "FORE.JK", "FORU.JK", "FPNI.JK", "ZONE.JK", "FUJI.JK", "FUTR.JK", "FWCT.JK", "GAMA.JK", "GDST.JK", "GDYR.JK", "GEMA.JK", "GEMS.JK", "GGRM.JK", "GGRP.JK", "GHON.JK", "GIAA.JK", "GJTL.JK", "GLOB.JK", "GLVA.JK", "GMFI.JK", "GMTD.JK", "GOLD.JK", "GOLF.JK", "GOLL.JK", "GOOD.JK", "GOTO.JK", "ZYRX.JK", "GPRA.JK", "GPSO.JK", "GRIA.JK", "GRPH.JK", "GRPM.JK", "GSMF.JK", "GTBO.JK", "GTRA.JK", "GTSI.JK", "GULA.JK", "GUNA.JK", "GWSA.JK", "GZCO.JK", "HADE.JK", "HAIS.JK", "HAJJ.JK", "HALO.JK", "HATM.JK", "HBAT.JK", "HDFA.JK", "HDIT.JK", "HEAL.JK", "HELI.JK", "HERO.JK", "HEXA.JK", "HGII.JK", "HILL.JK", "HITS.JK", "HKMU.JK", "HMSP.JK", "HOKI.JK", "HOME.JK", "HOMI.JK", "HOPE.JK", "HOTL.JK", "HRME.JK", "HRTA.JK", "HRUM.JK", "HUMI.JK", "HYGN.JK", "IATA.JK", "IBFN.JK", "IBOS.JK", "IBST.JK", "ICBP.JK", "ICON.JK", "IDEA.JK", "IDPR.JK", "IFII.JK", "IFSH.JK", "IGAR.JK", "IIKP.JK", "IKAI.JK", "IKAN.JK", "IKBI.JK", "IKPM.JK", "IMAS.JK", "IMJS.JK", "IMPC.JK", "INAF.JK", "INAI.JK", "INCF.JK", "INCI.JK", "INCO.JK", "INDF.JK", "INDO.JK", "INDR.JK", "INDS.JK", "INDX.JK", "INDY.JK", "INET.JK", "INKP.JK", "INOV.JK", "INPC.JK", "INPP.JK", "INPS.JK", "INRU.JK", "INTA.JK", "INTD.JK", "INTP.JK", "IOTF.JK", "IPAC.JK", "IPCC.JK", "IPCM.JK", "IPOL.JK", "IPPE.JK", "IPTV.JK", "IRRA.JK", "IRSX.JK", "ISAP.JK", "ISAT.JK", "ISEA.JK", "ISSP.JK", "ITIC.JK", "ITMA.JK", "ITMG.JK", "JARR.JK", "JAST.JK", "JATI.JK", "JAWA.JK", "JAYA.JK", "JECC.JK", "JGLE.JK", "JIHD.JK", "JKON.JK", "JMAS.JK", "JPFA.JK", "JRPT.JK", "JSKY.JK", "JSMR.JK", "JSPT.JK", "JTPE.JK", "KAEF.JK", "KAQI.JK", "KARW.JK", "KAYU.JK", "KBAG.JK", "KBLI.JK", "KBLM.JK", "KBLV.JK", "KBRI.JK", "KDSI.JK", "KDTN.JK", "KEEN.JK", "KEJU.JK", "KETR.JK", "KIAS.JK", "KICI.JK", "KIJA.JK", "KING.JK", "KINO.JK", "KIOS.JK", "KJEN.JK", "KKES.JK", "KKGI.JK", "KLAS.JK", "KLBF.JK", "KLIN.JK", "KMDS.JK", "KMTR.JK", "KOBX.JK", "KOCI.JK", "KOIN.JK", "KOKA.JK", "KONI.JK", "KOPI.JK", "KOTA.JK", "KPIG.JK", "KRAS.JK", "KREN.JK", "KRYA.JK", "KSIX.JK", "KUAS.JK", "LABA.JK", "LABS.JK", "LAJU.JK", "LAND.JK", "LAPD.JK", "LCGP.JK", "LCKM.JK", "LEAD.JK", "LFLO.JK", "LIFE.JK", "LINK.JK", "LION.JK", "LIVE.JK", "LMAS.JK", "LMAX.JK", "LMPI.JK", "LMSH.JK", "LOPI.JK", "LPCK.JK", "LPGI.JK", "LPIN.JK", "LPKR.JK", "LPLI.JK", "LPPF.JK", "LPPS.JK", "LRNA.JK", "LSIP.JK", "LTLS.JK", "LUCK.JK", "LUCY.JK", "MABA.JK", "MAGP.JK", "MAHA.JK", "MAIN.JK", "MANG.JK", "MAPA.JK", "MAPB.JK", "MAPI.JK", "MARI.JK", "MARK.JK", "MASB.JK", "MAXI.JK", "MAYA.JK", "MBAP.JK", "MBMA.JK", "MBSS.JK", "MBTO.JK", "MCAS.JK", "MCOL.JK", "MCOR.JK", "MDIA.JK", "MDIY.JK", "MDKA.JK", "MDKI.JK", "MDLA.JK", "MDLN.JK", "MDRN.JK", "MEDC.JK", "MEDS.JK", "MEGA.JK", "MEJA.JK", "MENN.JK", "MERI.JK", "MERK.JK", "META.JK", "MFMI.JK", "MGLV.JK", "MGNA.JK", "MGRO.JK", "MHKI.JK", "MICE.JK", "MIDI.JK", "MIKA.JK", "MINA.JK", "MINE.JK", "MIRA.JK", "MITI.JK", "MKAP.JK", "MKNT.JK", "MKPI.JK", "MKTR.JK", "MLBI.JK", "MLIA.JK", "MLPL.JK", "MLPT.JK", "MMIX.JK", "MMLP.JK", "MNCN.JK", "MOLI.JK", "MORA.JK", "MPIX.JK", "MPMX.JK", "MPOW.JK", "MPPA.JK", "MPRO.JK", "MPXL.JK", "MRAT.JK", "MREI.JK", "MSIE.JK", "MSIN.JK", "MSJA.JK", "MSKY.JK", "MSTI.JK", "MTDL.JK", "MTEL.JK", "MTFN.JK", "MTLA.JK", "MTMH.JK", "MTPS.JK", "MTRA.JK", "MTSM.JK", "MTWI.JK", "MUTU.JK", "MYOH.JK", "MYOR.JK", "MYTX.JK", "NAIK.JK", "NANO.JK", "NASA.JK", "NASI.JK", "NATO.JK", "NAYZ.JK", "NCKL.JK", "NELY.JK", "NEST.JK", "NETV.JK", "NFCX.JK", "NICE.JK", "NICK.JK", "NICL.JK", "NIKL.JK", "NINE.JK", "NIRO.JK", "NISP.JK", "NOBU.JK", "NPGF.JK", "NRCA.JK", "NSSS.JK", "NTBK.JK", "NUSA.JK", "NZIA.JK", "OASA.JK", "OBAT.JK", "OBMD.JK", "OCAP.JK", "OILS.JK", "OKAS.JK", "OLIV.JK", "OMED.JK", "OMRE.JK", "OPMS.JK", "PACK.JK", "PADA.JK", "PADI.JK", "PALM.JK", "PAMG.JK", "PANI.JK", "PANR.JK", "PANS.JK", "PART.JK", "PBID.JK", "PBRX.JK", "PBSA.JK", "PCAR.JK", "PDES.JK", "PDPP.JK", "PEGE.JK", "PEHA.JK", "PEVE.JK", "PGAS.JK", "PGEO.JK", "PGJO.JK", "PGLI.JK", "PGUN.JK", "PICO.JK", "PIPA.JK", "PJAA.JK", "PJHB.JK", "PKPK.JK", "PLAN.JK", "PLAS.JK", "PLIN.JK", "PMJS.JK", "PMMP.JK", "PMUI.JK", "PNBN.JK", "PNBS.JK", "PNGO.JK", "PNIN.JK", "PNLF.JK", "PNSE.JK", "POLA.JK", "POLI.JK", "POLL.JK", "POLU.JK", "POLY.JK", "POOL.JK", "PORT.JK", "POSA.JK", "POWR.JK", "PPGL.JK", "PPRE.JK", "PPRI.JK", "PPRO.JK", "PRAY.JK", "PRDA.JK", "PRIM.JK", "PSAB.JK", "PSAT.JK", "PSDN.JK", "PSGO.JK", "PSKT.JK", "PSSI.JK", "PTBA.JK", "PTDU.JK", "PTIS.JK", "PTMP.JK", "PTMR.JK", "PTPP.JK", "PTPS.JK", "PTPW.JK", "PTRO.JK", "PTSN.JK", "PTSP.JK", "PUDP.JK", "PURA.JK", "PURE.JK", "PURI.JK", "PWON.JK", "PYFA.JK", "PZZA.JK", "RAAM.JK", "RAFI.JK", "RAJA.JK", "RALS.JK", "RANC.JK", "RATU.JK", "RBMS.JK", "RCCC.JK", "RDTX.JK", "REAL.JK", "RELF.JK", "RELI.JK", "RGAS.JK", "RICY.JK", "RIGS.JK", "RIMO.JK", "RISE.JK", "RLCO.JK", "RMKE.JK", "RMKO.JK", "ROCK.JK", "RODA.JK", "RONY.JK", "ROTI.JK", "RSCH.JK", "RSGK.JK", "RUIS.JK", "RUNS.JK", "SAFE.JK", "SAGE.JK", "SAME.JK", "SAMF.JK", "SAPX.JK", "SATU.JK", "SBAT.JK", "SBMA.JK", "SCCO.JK", "SCMA.JK", "SCNP.JK", "SCPI.JK", "SDMU.JK", "SDPC.JK", "SDRA.JK", "SEMA.JK", "SFAN.JK", "SGER.JK", "SGRO.JK", "SHID.JK", "SHIP.JK", "SICO.JK", "SIDO.JK", "SILO.JK", "SIMA.JK", "SIMP.JK", "SINI.JK", "SIPD.JK", "SKBM.JK", "SKLT.JK", "SKRN.JK", "SKYB.JK", "SLIS.JK", "SMAR.JK", "SMBR.JK", "SMCB.JK", "SMDM.JK", "SMDR.JK", "SMGA.JK", "SMGR.JK", "SMIL.JK", "SMKL.JK", "SMKM.JK", "SMLE.JK", "SMMA.JK", "SMMT.JK", "SMRA.JK", "SMRU.JK", "SMSM.JK", "SNLK.JK", "SOCI.JK", "SOFA.JK", "SOHO.JK", "SOLA.JK", "SONA.JK", "SOSS.JK", "SOTS.JK", "SOUL.JK", "SPMA.JK", "SPRE.JK", "SPTO.JK", "SQMI.JK", "SRAJ.JK", "SRIL.JK", "SRSN.JK", "SRTG.JK", "SSIA.JK", "SSMS.JK", "SSTM.JK", "STAA.JK", "STAR.JK", "STRK.JK", "STTP.JK", "SUGI.JK", "SULI.JK", "SUNI.JK", "SUPA.JK", "SUPR.JK", "SURE.JK", "SURI.JK", "SWAT.JK", "SWID.JK", "TALF.JK", "TAMA.JK", "TAMU.JK", "TAPG.JK", "TARA.JK", "TAXI.JK", "TAYS.JK", "TBIG.JK", "TBLA.JK", "TBMS.JK", "TCID.JK", "TCPI.JK", "TDPM.JK", "TEBE.JK", "TECH.JK", "TELE.JK", "TFAS.JK", "TFCO.JK", "TGKA.JK", "TGRA.JK", "TGUK.JK", "TIFA.JK", "TINS.JK", "TIRA.JK", "TIRT.JK", "TKIM.JK", "TLDN.JK", "TLKM.JK", "TMAS.JK", "TMPO.JK", "TNCA.JK", "TOBA.JK", "TOOL.JK", "TOPS.JK", "TOSK.JK", "TOTL.JK", "TOTO.JK", "TOWR.JK", "TOYS.JK", "TPMA.JK", "TRAM.JK", "TRGU.JK", "TRIL.JK", "TRIM.JK", "TRIN.JK", "TRIO.JK", "TRIS.JK", "TRJA.JK", "TRON.JK", "TRST.JK", "TRUE.JK", "TRUK.JK", "TRUS.JK", "TSPC.JK", "TUGU.JK", "TYRE.JK", "UANG.JK", "UCID.JK", "UDNG.JK", "UFOE.JK", "ULTJ.JK", "UNIC.JK", "UNIQ.JK", "UNIT.JK", "UNSP.JK", "UNTD.JK", "UNTR.JK", "UNVR.JK", "URBN.JK", "UVCR.JK", "VAST.JK", "VERN.JK", "VICI.JK", "VICO.JK", "VINS.JK", "VISI.JK", "VIVA.JK", "VKTR.JK", "VOKS.JK", "VRNA.JK", "VTNY.JK", "WAPO.JK", "WEGE.JK", "WEHA.JK", "WGSH.JK", "WICO.JK", "WIDI.JK", "WIFI.JK", "WIIM.JK", "WIKA.JK", "WINE.JK", "WINR.JK", "WINS.JK", "WIRG.JK", "WMPP.JK", "WMUU.JK", "WOMF.JK", "WOOD.JK", "WOWS.JK", "WSBP.JK", "WSKT.JK", "WTON.JK", "YELO.JK", "YOII.JK", "YPAS.JK", "YULE.JK", "YUPI.JK", "ZATA.JK", "ZBRA.JK", "ZINC.JK"]

# --- MAIN LOGIC ---
if st.button("🔍 Jalankan Scanner"):
    results = []
    status_area = st.empty()
    progress_bar = st.progress(0)
    
    # BATCH PROCESSING (Menghindari timeout)
    batch_size = 50
    total_stocks = len(default_stocks)
    
    for i in range(0, total_stocks, batch_size):
        batch = default_stocks[i : i + batch_size]
        status_area.info(f"⏳ Scanning Batch {i//batch_size + 1}: {batch[0]} ...")
        
        # Download Batch
        try:
            data = yf.download(batch, period="1y", interval="1d", group_by='ticker', progress=False, timeout=20)
        except Exception as e:
            st.warning(f"Batch {i//batch_size + 1} gagal diunduh: {e}")
            continue

        for ticker in batch:
            try:
                # Cek apakah data tersedia
                if ticker not in data.columns.levels[0]: continue
                
                df_ticker = data[ticker].dropna(subset=['Close'])
                if len(df_ticker) < 20: continue

                # Indikator
                df_ticker["SMA20"] = ta.sma(df_ticker["Close"], length=20)
                df_ticker["SMA200"] = ta.sma(df_ticker["Close"], length=200)
                df_ticker["RSI"] = ta.rsi(df_ticker["Close"], length=14)
                df_ticker.fillna(0, inplace=True)
                
                last = df_ticker.iloc[-1]
                price = float(last['Close'])
                sma20 = float(last['SMA20'])
                sma200 = float(last['SMA200'])
                rsi = float(last['RSI'])
                
                # Volume & Performance
                vol_today = float(last['Volume'])
                avg_vol = float(df_ticker['Volume'].tail(20).mean())
                vol_ratio = vol_today / avg_vol if avg_vol > 0 else 0
                
                prev_1m_idx = -21 if len(df_ticker) >= 21 else 0
                prev_1m_price = df_ticker.iloc[prev_1m_idx]['Close']
                pct_1m = ((price - prev_1m_price) / prev_1m_price) * 100

                # --- FILTER LOGIC ---
                # Syarat: Harga di atas SMA20, RSI sesuai filter, Vol sesuai filter
                is_uptrend = (price > sma20) 
                # (Optional: price > sma200 jika ingin sangat ketat)
                
                if is_uptrend and rsi >= rsi_min and vol_ratio >= vol_ratio_min and pct_1m >= pct_1m_min:
                    
                    # Cek Market Cap (Hanya untuk yang lolos teknikal)
                    t_info = yf.Ticker(ticker).info
                    mcap = t_info.get('marketCap', 0) / 1e12
                    
                    if mcap >= mcap_min:
                        # Risk/Money Management
                        sl_price = sma20 * 0.98
                        risk_per_sh = price - sl_price
                        if risk_per_sh <= 0: # Proteksi jika SMA20 di atas harga
                            sl_price = price * 0.95
                            risk_per_sh = price - sl_price
                        
                        tp_price = price + (risk_per_sh * 2)
                        
                        amt_risk = total_budget * (risk_per_trade / 100)
                        lots = int((amt_risk / risk_per_sh) // 100) if risk_per_sh > 0 else 0
                        
                        results.append({
                            "Ticker": ticker.replace(".JK", ""),
                            "Price": int(price),
                            "RSI": round(rsi, 1),
                            "Vol Ratio": round(vol_ratio, 2),
                            "SL": int(sl_price),
                            "TP": int(tp_price),
                            "Lot": lots,
                            "MCap (T)": round(mcap, 1)
                        })
            except:
                continue
        
        progress_bar.progress((i + batch_size) / total_stocks if (i + batch_size) < total_stocks else 1.0)

    status_area.empty()
    
    # --- OUTPUT ---
    if results:
        st.success(f"✅ Ditemukan {len(results)} saham potensial!")
        df_final = pd.DataFrame(results)
        st.dataframe(df_final, use_container_width=True, hide_index=True)
        
        if use_telegram:
            msg = f"🚀 *IDX SIGNAL PRO*\n"
            for r in results:
                msg += f"• *{r['Ticker']}*: Rp{r['Price']} | TP:{r['TP']} | SL:{r['SL']} | *{r['Lot']} Lot*\n"
            send_telegram_msg(msg)
    else:
        st.warning("⚠️ Tidak ada saham memenuhi kriteria. Coba turunkan Min RSI atau Vol Ratio.")

st.divider()
st.caption(f"© 2026 jamilstempel.com | Data: Yahoo Finance | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
