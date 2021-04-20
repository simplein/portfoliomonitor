import os
import json
import pandas as pd
import easyquotation
import requests

def getportfoliodataframe():    
    ports = json.loads(os.getenv('ports_json'))
    dfs=pd.DataFrame()
    for port in ports[:]:
        df=[[stock, number] for stock, number in port['port'].items()]
        df = pd.DataFrame(df, columns = ['code','number'])
        df['account']=port['account']
        df = df.set_index(['account','code'])
        dfs= dfs.append(df)
    return dfs

def gethq(pool):
    quotation = easyquotation.use('qq')
    hq=[[code,val['name'],val['now'],val['涨跌']] for code, val in quotation.stocks(pool).items()]
    hq.append(['CASH','现金',1,0])
    hq = pd.DataFrame(hq, columns = ['code','name','pricenow','change']).set_index('code')    
    hq['preclose'] = hq['pricenow'] - hq['change']
    hq['pctchange%'] = round(hq['change'] / hq['preclose'] *100, 2)
    return hq

def getNAVtable():
    def transcode(strs):
        return strs[:6]
    ports = getportfoliodataframe().reset_index()
    ports['code'] = ports['code'].apply(transcode)
    ports2 = pd.pivot_table(ports, index='code',values='number',aggfunc=sum)
    pool = ports2.index.to_list()
    pool.remove('CASH')
    df = pd.concat([gethq(pool),ports2],axis = 1)    
    df['preamount'] = df['preclose'] * df['number']
    df['amount'] = df['pricenow'] * df['number']
    return df

def getbmhq():
    quotation = easyquotation.use('qq')
    hq = quotation.stocks('sh000300')['000300']
    r = hq['涨跌']/(hq['now']-hq['涨跌'])
    return r

NAVtable = getNAVtable()
amount = NAVtable['amount'].sum()
preamount = NAVtable['preamount'].sum()
r_p = amount/preamount-1; r_bm = getbmhq()
er = (r_p+1)/(r_bm+1)-1
message =   'NAV lastday is            ' + format(round(preamount,2), ',') + '\n' + \
            'NAV now is                ' + format(round(amount,2), ',')  + '\n' + \
            'portfolio pctchange is    %.4f%%' % round(r_p*100,4) + '\n' + \
            'csi300 pctchange is       %.4f%%' % round(r_bm*100,4) + '\n' + \
            'excess return is          %.4f%%' % round(er*100,4)
print(message)

token = os.getenv('xtstoken')
txsdata = {'text':'re_p: %.4f%%, re_b: %.4f%%。' %(round(r_p*100,4),round(r_bm*100,4)),'desp':message}
requests.post('http://wx.xtuis.cn/' + token + '.send', data = txsdata) 