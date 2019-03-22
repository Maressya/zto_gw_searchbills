#-*- coding: utf-8 -*
import datetime
import time
import json
import jsonpath
import urllib.request
import urllib.parse
from lxml import etree
import cx_Oracle
import xlrd


#获取请求url
search_bill_url = "https://hdgateway.zto.com/WayBill_GetDetail"

#请求头
headers = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Connection': 'keep-alive',
    'Content-Length': '23',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Host': 'hdgateway.zto.com',
    'Origin': 'https://www.zto.com',
    'Referer': 'https://www.zto.com/express/expressCheck.html?txtBill=73109972743258',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
    'x-clientCode': 'pc',
}
'''
    读取xlsx数据，获取列表内容
'''
# ExcelFile=xlrd.open_workbook(r'C:\Users\Administrator\Desktop\zto_searchbill\zt_bills.xlsx')
# sheet=ExcelFile.sheet_by_name('Sheet1')
# rowNum = sheet.nrows
# colNum = sheet.ncols
# list = []
# for i in range(1,rowNum):
#     rowlist = []
#     for j in range(colNum):
#         rowlist.append(sheet.cell_value(i, j))
#         list.append(rowlist[0])
# # print(list)
# bill_list = [x.strip() for x in list if x.strip()!='']
# print(bill_list)
# # print(bill_list[:10])
# # print(len(bill_list[:10]))

'''
    处理邮递单号数据
    单号列表每10个遍历提取
'''
bill_lists = [str(x) for x in range(73109972755000,73109972756000)]
# print(bill_lists)
bill_lists = [bill_lists[i:i+10] for i in range(0,len(bill_lists),10)]
# print(bill_lists)
# for bill_list in bill_lists:
#     print(bill_list)
crawl_date = datetime.datetime.now().strftime('%Y_%m_%d')
print('爬取时间：'+crawl_date)
crawl_datetime = time.strftime('%Y/%m/%d %H:%M:%S ',time.localtime(time.time()))
print("当前时间： ",crawl_datetime)
tab_name = 'table_name'
db_ora = cx_Oracle.connect('username/password@ip/token')
cursor = db_ora.cursor()


'''
    1.处理请求
    2.获取响应文本
'''
def handle_request(url,bill):
    data = {
        'billCode': bill,
    }
    print("爬取单号：%s..." % (bill))
    try:
        request = urllib.request.Request(url=url,data=urllib.parse.urlencode(data).encode('utf-8'),headers=headers)
    except urllib.error.URLError as e:
        print("单号：%s 无效！" % (bill))
        print(e.reason)
    try:
        response = urllib.request.urlopen(request)
        content = response.read().decode('utf-8')
        print(content)
        print("爬取结束...")
        return content
    except urllib.error.URLError as e:
        print("单号：%s 无效！" % (bill))
        print(e.reason,e.code, e.headers, sep='\n')


'''
    解析response
    生成json字符串
    写入json文件
'''
def parse_content(content,bill):
    str_bill = json.dumps(json.loads(content),ensure_ascii=False)
    # with open('zt.json','a',encoding='utf-8') as fp:
    #     print("录入单号：%s，到json文件中..." % (bill))
    #     if bill == bill_list[0]:
    #             fp.write('[' + '\n' + str_bill + ',' + '\n')
    #     else:
    #         if bill == bill_list[len(bill_list)-1]:
    #             fp.write(str_bill + '\n' + ']')
    #         else:
    #             fp.write(str_bill + ',' + '\n')
    #     print("已经写入json文件...")
    #     fp.close()


'''
    获取的json数据，提取相应的key
    拿到相应的字段
'''
def parse_json(content):
    billcode = jsonpath.jsonpath(json.loads(content), '$..billCode')[0]
    # print(billcode)
    total_days = jsonpath.jsonpath(json.loads(content), '$..billPrescription')[0]
    # print(total_days)
    date_list = jsonpath.jsonpath(json.loads(content), '$..scanDate')
    # print(date_list)
    print(len(date_list))
    state_list = jsonpath.jsonpath(json.loads(content), '$..stateDescription')
    # print(state_list)
    print(len(state_list))
    return billcode,total_days,date_list,state_list


def main():
    for bill_list in bill_lists:
        for bill_no in bill_list:
            print("获取单号：%s" % (bill_no))
            content = handle_request(search_bill_url,bill_no)
            # print(content)
            #通过result判断单号是否能查到轨迹内容
            result = jsonpath.jsonpath(json.loads(content), '$..result')[0]
            # print(jsonpath.jsonpath(json.loads(content), '$..result')[0])
            # print(type(result))

            if result != None:
                parse_content(content,bill_no)
                billcode, total_days, date_list, state_list = parse_json(handle_request(search_bill_url,bill_no))
                print(billcode,total_days,date_list,state_list)

                for num in range(len(date_list)):
                    insert_sql = 'INSERT INTO %s (item_no,do_time,do_remark,sy_time) VALUES (:1, :2, :3, :4)' % (tab_name)
                    val = (billcode, date_list[num], state_list[num], crawl_datetime)
                    # print(insert_sql)
                    cursor.execute(insert_sql, val)
                    # print(val)
                    db_ora.commit()
                    print("插入成功！")
            else:
                print("单号无效!")

            print('*' * 999)
            time.sleep(3)

    cursor.close()
    db_ora.close()


if __name__ == '__main__':
    main()
