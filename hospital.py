# -*- coding: utf8 -*-

import requests
from bs4 import BeautifulSoup
from xml.etree import ElementTree

url = 'http://www.a-hospital.com/w/'
site = 'http://www.a-hospital.com'

headers = {
    'User-Agent': 'My User Agent 1.0',
    'From': 'xiaozhuyfk@gmail.com'  # This is another valid field
}

tags = [
    u'医院名称'.encode('utf-8'),
    u'别称'.encode('utf-8'),
    u'医院等级'.encode('utf-8'),
    u'经营方式'.encode('utf-8'),
    u'重点科室'.encode('utf-8'),
    u'省'.encode('utf-8'),
    u'市'.encode('utf-8'),
    u'区'.encode('utf-8'),
    u'医院地址'.encode('utf-8'),
    u'医院网站'.encode('utf-8'),
    u'联系电话'.encode('utf-8'),
    u'电子邮箱'.encode('utf-8'),
]

direct_city = [
    u'北京市'.encode('utf-8'),
    u'上海市'.encode('utf-8'),
    u'重庆市'.encode('utf-8'),
    u'天津市'.encode('utf-8')
]

province_list = [
    #u'江苏省'.encode('utf-8'),
    #u'广东省'.encode('utf-8'),
    #u'山东省'.encode('utf-8'),
    #u'辽宁省'.encode('utf-8'),
    u'河北省'.encode('utf-8'),
    u'河南省'.encode('utf-8'),
    u'四川省'.encode('utf-8'),
    u'黑龙江省'.encode('utf-8'),
    u'山西省'.encode('utf-8'),
    u'湖北省'.encode('utf-8'),
    u'湖南省'.encode('utf-8'),
    u'陕西省'.encode('utf-8'),
    u'浙江省'.encode('utf-8'),
    u'云南省'.encode('utf-8'),
    u'吉林省'.encode('utf-8'),
    u'安徽省'.encode('utf-8'),
    u'广西壮族自治区'.encode('utf-8'),
    u'江西省'.encode('utf-8'),
    u'福建省'.encode('utf-8'),
    u'新疆维吾尔自治区'.encode('utf-8'),
    u'内蒙古自治区'.encode('utf-8'),
    u'甘肃省'.encode('utf-8'),
    u'贵州省'.encode('utf-8'),
    u'海南省'.encode('utf-8'),
    u'青海省'.encode('utf-8'),
    u'宁夏回族自治区'.encode('utf-8'),
    u'西藏自治区'.encode('utf-8'),
]


class Hospital(object):

    def __init__(self, attributes):
        self.attributes = attributes

    def __eq__(self, other):
        return (self.attributes[u'医院地址'.encode('utf-8')] == other.attributes[u'医院地址'.encode('utf-8')])

    def __hash__(self):
        return hash(self.attributes[u'医院地址'.encode('utf-8')])

    def __getitem__(self, key):
        if isinstance(key, unicode): key = key.encode('utf-8')
        return self.attributes.get(key, "")

    def __setitem__(self, key, value):
        if isinstance(key, unicode): key = key.encode('utf-8')
        if isinstance(value, unicode): value = value.encode('utf-8')
        self.attributes[key] = value


def parse_hospital_data(li):
    name = li.find('a').string.encode('utf-8')
    text = li.get_text().strip().split('\n')
    alias = text[0].encode('utf-8')
    alias = alias[len(name):]
    rest = text[1:]
    attr_map = {
        u'医院名称'.encode('utf-8') : name,
        u'别称'.encode('utf-8') : alias
    }

    for attr in rest:
        if attr:
            key = attr[:4].encode('utf-8')
            value = attr[5:].encode('utf-8')
            attr_map[key] = value

    return Hospital(attr_map)

def parse_district_data(province, city, district, url_path = None):
    print 'Processing district data for', province, city, district

    if isinstance(province, unicode): province = province.encode('utf-8')
    if isinstance(city, unicode): city = city.encode('utf-8')
    if isinstance(district, unicode): district = district.encode('utf-8')

    if url_path is None:
        url_path = url + city + district + u'医院列表'.encode('utf-8')

    response = requests.get(url_path, headers = headers)
    html = response.content

    soup = BeautifulSoup(html, 'html.parser')
    html_lists = None
    for ul in soup.find_all('ul'):
        if ul.find('ul'):
            html_lists = ul
            break
    if html_lists is None:
        return []
    
    hospitals = []
    record = set([])
    for li in html_lists.find_all('li', recursive = False):
        hospital = parse_hospital_data(li)
        hospital[u'省'.encode('utf-8')] = province
        hospital[u'市'.encode('utf-8')] = city
        hospital[u'区'.encode('utf-8')] = district
        if (hospital not in record):
            hospitals.append(hospital)
            record.add(hospital)

    return hospitals


def parse_city_data(province, city, url_path = None):
    if isinstance(province, unicode): province = province.encode('utf-8')
    if isinstance(city, unicode): city = city.encode('utf-8')

    if url_path is None:
        url_path = url + city + u'医院列表'.encode('utf-8')
    response = requests.get(url_path, headers = headers)
    html = response.content
    soup = BeautifulSoup(html, 'html.parser')
    
    result = []
    for li in soup.find('ul').find_all('li'):
        href = li.find('a').get('href', None)
        district = li.get_text()

        if (href is None): continue

        if (district[-2:] == u'医院'):
            district = district[:-2]

        result += parse_district_data(
            province, 
            city, 
            district, 
            site + href)

    return result



def parse_province_data(province):
    if isinstance(province, unicode): province = province.encode('utf-8')

    url_path = url + province + u'医院列表'.encode('utf-8')
    response = requests.get(url_path, headers = headers)
    html = response.content
    soup = BeautifulSoup(html, 'html.parser')

    city_lists = None
    for p in soup.find_all('p'):
        if (p.find('a')):
            city_lists = p
            break
    
    result = []
    for a in city_lists.find_all('a'):
        if (province in direct_city):
            result += parse_district_data(
                province, 
                province, 
                a.get_text(),
                site + a['href'])
        else:
            result += parse_city_data(
                province, 
                a.get_text())

    return result


def create_excel(file_name, hospitals):
    import xlsxwriter
    workbook = xlsxwriter.Workbook(file_name)
    format = workbook.add_format()
    format.set_text_wrap()

    worksheet = workbook.add_worksheet()

    cols = len(tags)
    worksheet.set_column(0, cols - 1, 30)
    for col in xrange(cols):
        worksheet.write(0, col, tags[col].decode('utf-8'), format)

    for i in xrange(len(hospitals)):
        hospital = hospitals[i]

        for col in xrange(cols):
            worksheet.write(i + 1, col, hospital[tags[col]].decode('utf-8'), format)

    workbook.close()


def main():
    #create_excel(process_data())
    #parse_district_data(u'上海市', u'上海市', u'长宁区')
    #parse_district_data(u'江苏省', u'苏州市', u'平江区')
    #parse_province_data(u'上海市')
    #parse_city_data(u'江苏省', u'无锡市')
    #create_excel(
    #    u'上海市'.encode('utf-8') + '.xlsx', 
    #    parse_province_data(u'上海市')
    #)

    #create_excel(
    #    u'北京市'.encode('utf-8') + '.xlsx',
    #    parse_province_data(u'北京市')
    #)
    #
    
    #for direct in direct_city:
    #    create_excel(direct + '.xlsx', parse_province_data(direct))

    for province in province_list:
        create_excel(province + '.xlsx', parse_province_data(province))


if __name__ == '__main__':
    main()
