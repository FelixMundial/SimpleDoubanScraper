"""
:keyword web scraping on douban books
"""
import importlib
import json
import os
import re
import ssl
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen, ProxyHandler, build_opener, install_opener, HTTPHandler

from bs4 import BeautifulSoup
from numpy import random

JSON_FILE_PATH = 'docs'
RETRYING_TIMES = 20

PLACEHOLDER_VALUE_NOT_SET = '暂无'
SUFFIX_JSON = '.json'

importlib.reload(sys)

# Some Predefined User Agents
USER_AGENTS = [
    {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6'},
    {'User-Agent': 'Mozilla/5.0 (Windows NT 6.2) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.12 Safari/535.11'},
    {'User-Agent': 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; Trident/6.0)'},
    {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:73.0) Gecko/20100101 Firefox/73.0'},
    {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1 Safari/605.1.15'},
    {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0'},
    {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'},
    {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.153 Safari/537.36'},
    {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:30.0) Gecko/20100101 Firefox/30.0'},
    {'User-Agent': 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; Win64; x64; Trident/6.0)'},
    {'User-Agent': 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)'},
    {'User-Agent': 'Mozilla/5.0 (compatible; Konqueror/3.5; Linux) KHTML/3.5.5 (like Gecko) (Kubuntu)'},
    {'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.12) Gecko/20070731 Ubuntu/dapper-security Firefox/1.5.0.12'},
    {'User-Agent': 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.7 (KHTML, like Gecko) Ubuntu/11.04 Chromium/16.0.912.77 Chrome/16.0.912.77 Safari/535.7'},
    {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:10.0) Gecko/20100101 Firefox/10.0'},
    {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36'}]

PROXY_IPS = []


def do_crawling_by_tag(book_tag, page_size, is_basic_tag):
    """
    根据豆瓣标签页类型及具体标签进行实际的数据爬取
    :param book_tag: 图书标签
    :param page_size: 需要爬取的页数
    :param is_basic_tag: 是否为豆瓣原生标签
    :return: 爬取的数据集（含有数据信息字典的一维列表）
    """
    page_count = 0
    book_info_map_list = []
    retrying_times = 0
    ssl._create_default_https_context = ssl._create_unverified_context

    while 1:
        if page_count == page_size:
            break
        print('Retrieving Information From Page %d' % (page_count + 1))
        if is_basic_tag:
            # 豆瓣读书预设标签列表
            # book_url='http://www.douban.com/tag/%E5%B0%8F%E8%AF%B4/book?start=0'
            # 单页15本书，start值为书的行数偏移量
            url = 'http://www.douban.com/tag/' + quote(book_tag) \
                  + '/book?start=' + str(page_count * 15)
        else:
            # 豆瓣读书用户自定义标签列表（更丰富）
            # book_url=''http://book.douban.com/tag/%E5%8F%A4%E5%B7%B4%E6%AF%94%E4%BC%A6?start=0&type=T''
            # 单页15本书，start值为书的行数偏移量
            url = 'http://book.douban.com/tag/' + quote(book_tag) \
                  + '?start=' + str(page_count * 15) + '&type=T'
        time.sleep(random.random() * 8)

        try:
            # proxy = ProxyHandler({'http': random.choice(PROXY_IPS)})
            # opener = build_opener(proxy, HTTPHandler)
            # opener.addheaders = [('User-Agent', random.choice(USER_AGENTS).get('User-Agent'))]
            # install_opener(opener)
            headers = random.choice(USER_AGENTS)

            # req = get(url, proxies={'http': random.choice(PROXY_IPS)}, headers=USER_AGENTS[np.random.randint(0, len(USER_AGENTS))])
            req = Request(url, headers=headers)
            source_code = urlopen(req).read()
            plain_text = str(source_code, 'utf-8')
        except (HTTPError, URLError) as e:
            print(e)
            continue

        soup = BeautifulSoup(plain_text, features="lxml")

        if is_basic_tag:
            div_book_list = soup.find('div', {'class': 'mod book-list'})
        else:
            div_book_list = soup.find('ul', {'class': 'subject-list'})

        retrying_times += 1
        # 无有效标签数据
        if div_book_list is None and page_count == 0:
            # 1. 标签错误，该标签下无有效内容
            if plain_text is not None:
                print("找不到任何图书...请确认所指定的标签是否正确或存在")
                break
            # 2. 连接错误，尝试重连
            if retrying_times < RETRYING_TIMES:
                print("尝试重新从豆瓣服务器获取响应...")
                continue
        if div_book_list is None or len(div_book_list) <= 1:
            break

        if is_basic_tag:
            for book_info in div_book_list.findAll('dd'):
                title = book_info.find('a', {'class': 'title'}).string.strip()
                print(title)
                desc = book_info.find('div', {'class': 'desc'}).string.strip()
                desc_list = desc.split('/')
                book_url = book_info.find('a', {'class': 'title'}).get('href')

                book_info = get_book_info(book_url)
                try:
                    author_info = '/'.join(desc_list[0:-3])
                except:
                    author_info = PLACEHOLDER_VALUE_NOT_SET
                try:
                    pub_info = '/'.join(desc_list[-3:])
                except:
                    pub_info = PLACEHOLDER_VALUE_NOT_SET
                # try:
                #     rating = book_info.find('span', {'class': 'rating_nums'}).string.strip()
                # except:
                #     rating = '0.0'
                # try:
                #     # raters_count = book_info.findAll('span')[2].string.strip()
                #     raters_count = get_book_info(book_url).get('ratersCount').strip('人评价')
                # except:
                #     raters_count = '0'
                book_comments = get_book_comments(book_url, False, 10)

                print("authorInfo:" + author_info + "; rating:" + str(book_info.get('averageRating')) + "(" + str(
                    book_info.get('ratersCount')) + ")" + "; pubInfo:" + pub_info + "; img:" + book_info.get('img')[0])
                book_info_map = {'title': title, 'bookUrl': book_url, 'authorInfo': author_info, 'pubInfo': pub_info,
                                 'bookInfo': book_info, 'comments': book_comments}
                book_info_map_list.append(book_info_map)
        else:
            for book_info in div_book_list.find_all('div', {'class': 'info'}):
                # 去掉标题区域的制表符
                title = re.sub(r'\s*', "", book_info.find('a').text.strip())
                print(title)
                desc = book_info.find('div', {'class': 'pub'}).string.strip()
                desc_list = desc.split('/')
                book_url = book_info.find('a').get('href')

                book_info = get_book_info(book_url)
                try:
                    author_info = '/'.join(desc_list[0:-3])
                except:
                    author_info = PLACEHOLDER_VALUE_NOT_SET
                try:
                    pub_info = '/'.join(desc_list[-3:])
                except:
                    pub_info = PLACEHOLDER_VALUE_NOT_SET
                # try:
                #     rating = book_info.find('span', {'class': 'rating_nums'}).string.strip()
                # except:
                #     rating = '0.0'
                # try:
                #     # raters_count = book_info.find('span', {'class': 'pl'}).string.strip('人评价')
                #     raters_count = get_book_info(book_url).get('ratersCount').strip('人评价')
                # except:
                #     raters_count = '0'
                book_comments = get_book_comments(book_url, False, 10)

                print("authorInfo:" + author_info + "; rating:" + str(book_info.get('averageRating')) + "(" + str(
                    book_info.get('ratersCount')) + ")" + "; pubInfo:" + pub_info + "; img:" + book_info.get('img')[0])
                book_info_map = {'title': title, 'bookUrl': book_url, 'authorInfo': author_info, 'pubInfo': pub_info,
                                 'bookInfo': book_info, 'comments': book_comments}
                book_info_map_list.append(book_info_map)

            retrying_times = 0  # Reset when valid information is received

        page_count += 1

    return book_info_map_list


def crawl_by_basic_tag(tag, page_size):
    """
    爬取预设标签列表数据
    :param tag: 图书标签
    """
    return do_crawling_by_tag(tag, page_size, True)


def crawl_by_user_tag(tag, page_size):
    """
    爬取用户自定义标签列表数据
    :param tag: 图书标签
    """
    return do_crawling_by_tag(tag, page_size, False)


# # book_url='http://book.douban.com/subject/6082808/?from=tag_all'
def get_book_info(book_url):
    """
    获取图书其他重要信息
    :param book_url: 图书详情页URL
    :return: 图书其他重要信息，格式为字典
    """
    plain_text = parse_book_url(book_url)
    soup = BeautifulSoup(plain_text, features="lxml")

    # 图书封面图URL（L和M两种尺寸）
    url_parent = soup.find('a', {'class': 'nbg'})
    cover_url = [url_parent.get('href'), url_parent.find('img').get('src')]

    # info_parent = soup.find('div', id='info').find_all('span', {'class': 'pl'})
    original_name = ''
    # for info_section_name in info_parent:
    #     if info_section_name.string.strip().find('原作名') != -1:
    #         if info_section_name.find_next() is not None:
    #             original_name = info_section_name.find_next().string  # 需获取该标签后的普通文本
    #         else:
    #             break

    # 图书评分
    ratings = []
    rating_parent = soup.find('div', {'class': 'rating_wrap clearbox'})
    average_rating = rating_parent.find('strong').string
    # raters_count = rating_parent.find('div', {'class': 'rating_sum'}).find_all('span')[1].string.strip()
    # 若评价人数不足 或 目前无人评价，则不统计评分信息
    test_rating_string = rating_parent.find('a', href='collections')
    if test_rating_string is None:
        test_rating_string = rating_parent.find('div', {'class': 'rating_sum'}).find('span')
    if average_rating == ' ' and (test_rating_string.string.find('评价') != -1 or test_rating_string is None):
        average_rating = 0.0
        raters_count = 0
    else:
        raters_count = rating_parent.find('a', {'class': 'rating_people'}).find_all('span')[0].string.strip()
        ratings_container = rating_parent.find_all('span', {'class': 'rating_per'})
        if len(ratings_container) == 5:
            ratings = [ratings_container[0].get_text(), ratings_container[1].get_text(),
                       ratings_container[2].get_text(), ratings_container[3].get_text(),
                       ratings_container[4].get_text()]

    # 图书与作者简介
    book_related_info_parent = soup.find('div', {'class': 'related_info'})
    book_intro_parent = book_related_info_parent.find_all('div', {'class': 'intro'})
    if len(book_intro_parent) == 3:
        book_intro = book_intro_parent[1].get_text().strip()  # 需将多个p标签内容拆分进列表
        author_intro = book_intro_parent[2].get_text().strip()
    elif len(book_intro_parent) == 2:
        book_intro = book_intro_parent[0].get_text().strip()
        author_intro = book_intro_parent[1].get_text().strip()
    else:
        book_intro = ''
        author_intro = ''

    # 图书目录
    book_toc_parent = book_related_info_parent.find('div', {'class': 'indent', 'id': re.compile(r'dir_\d*_full')})
    if book_toc_parent is not None:
        book_toc = book_toc_parent.get_text().strip()  # · · · · · ·     (收起)
    else:
        book_toc = ''

    return {'img': cover_url, 'originalName': original_name,
            'averageRating': average_rating, 'ratersCount': raters_count, 'ratings': ratings,
            'bookIntro': book_intro, 'authorIntro': author_intro, 'bookToc': book_toc}


def get_book_comments(book_url, sort_by_time, list_size):
    """
    获取图书评论
    :param book_url: 图书评论页URL
    :param sort_by_time: 是否只看最新评论
    :param list_size: 获取评论条数
    :return: 评论信息列表
    """
    comment_info = {}
    comment_info_list = []
    list_count = 0
    # 最新评论
    if sort_by_time:
        plain_text = parse_book_url(book_url + "/comments/new")
    # 最热评论
    else:
        plain_text = parse_book_url(book_url + "/comments/hot")

    soup = BeautifulSoup(plain_text, features="lxml")
    comments_count = soup.find('span', id='total-comments').string.strip()
    comment_info['commentsCount'] = comments_count
    if re.findall(r'\d+', comments_count) != '0':
        comments_container = soup.find('div', {'id': 'comments', 'class': 'comment-list'})
        for comments_parent in comments_container.find_all('li', {'class': 'comment-item'}):
            if list_count >= list_size or comments_parent.find('p', {'class': 'blank-tip'}) is not None:
                break
            comment_info_parent = comments_parent.find('span', {'class': 'comment-info'})
            comment_info_user = comment_info_parent.find('a').get_text()
            comment_info_rating = comment_info_parent.find_all('span')
            if len(comment_info_rating) == 2:
                comment_info_rating_score = comment_info_rating[0].get('title')
                comment_info_rating_time = comment_info_rating[1].get_text()
            else:
                comment_info_rating_score = 0.0
                comment_info_rating_time = ''
            comment_votes = comments_parent.find('span', {'class': 'comment-vote'}).find('span', {
                'class': 'vote-count'}).get_text()
            comment_content = comments_parent.find('p', {'class': 'comment-content'}).find('span').get_text().strip()
            comment_info_list.append({'user': comment_info_user, 'ratingScore': comment_info_rating_score,
                                      'ratingTime': comment_info_rating_time,
                                      'thumbsUpCount': comment_votes, 'content': comment_content})
            list_count += 1
        comment_info['commentsList'] = comment_info_list
    return comment_info


def parse_book_url(book_url):
    """
    获取图书详情页面数据
    :param book_url: 图书详情页URL
    :return: 图书详情页面数据字符串
    """
    try:
        headers = random.choice(USER_AGENTS)
        req = Request(book_url, headers=headers)
        source_code = urlopen(req).read()
        plain_text = str(source_code, 'utf-8')
        return plain_text
    except (HTTPError, URLError) as e:
        print(e)


def crawl_by_tags(book_tag_lists, page_size, is_basic_tag):
    """
    根据豆瓣api类型及标签进行爬取豆瓣数据
    :param book_tag_lists: 标签列表
    :param is_basic_tag: 是否为豆瓣原生标签
    """
    for book_tag in book_tag_lists:
        if is_basic_tag:
            book_info_map_list = crawl_by_basic_tag(book_tag, page_size)
        else:
            book_info_map_list = crawl_by_user_tag(book_tag, page_size)
        # 此处暂不作排序
        # book_info_map_list = sorted(book_info_map_list, key=lambda x: x[1], reverse=True)
        if book_info_map_list is not None and len(book_info_map_list) != 0:
            export_data_to_json(book_info_map_list, book_tag, JSON_FILE_PATH, False)


def export_data_to_json(list, book_tag, file_path_prefix, is_basic_tag):
    """
    将列表数据输出JSON文件
    :param list: 爬取的数据集
    :param book_tag: 数据集对应标签
    :param file_path_prefix: 输出JSON文件路径前缀
    :param is_basic_tag: 是否为豆瓣原生标签
    :return:
    """
    if is_basic_tag:
        json_path = file_path_prefix + "/" + book_tag + "_0" + SUFFIX_JSON
    else:
        json_path = file_path_prefix + "/" + book_tag + SUFFIX_JSON
    with open(json_path, "w") as f:
        f.write(json.dumps(list, ensure_ascii=False))
        # json.dump(list, f)


if __name__ == '__main__':
    if not os.path.exists(JSON_FILE_PATH):
        os.makedirs(JSON_FILE_PATH)
    # https://www.douban.com/tag//?source=topic_search
    # book_tag_lists = ['香港', '台湾', '北京', '上海', '日本', '韩国', '英国', '意大利', '清迈', '巴黎', '欧洲', '火车']
    # book_tag_lists = ['哲学', '建筑', '古建筑', '寺庙', '宗教', '人文', '历史', '博物馆']
    book_tag_lists = ['拜占庭', '古巴比伦', '古埃及']
    # 只测试爬取2页
    crawl_by_tags(book_tag_lists, 2, False)