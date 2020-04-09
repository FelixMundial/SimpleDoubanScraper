## 豆瓣读书爬虫

基于https://github.com/lanbing510/DouBanSpider开源部分代码进行大规模重构，并将Python版本升级为3.8

旨在提供api级别的接口，目前可将数据导出为JSON格式（暂未集成Web或Java服务）

#### Feature
 - 爬取豆瓣读书默认标签下图书列表（如https://www.douban.com/tag/%E7%BD%97%E9%A9%AC/?source=topic_search）及用户自定义标签下图书列表（如https://book.douban.com/tag/%E5%8F%A4%E5%B7%B4%E6%AF%94%E4%BC%A6）
 - 导出JSON格式数据，数据涵盖图书概要、评分、图书与作者简介以及用户评论等（可插拔）
 
#### Todo List
 > 接口部分
 - 借助Tornado等Python Web框架对服务进行封装，并最终以独立Web服务的形式接入Spring Cloud注册中心
 > Python服务代码部分
 - 集成UA池（如https://github.com/hellysmile/fake-useragent）与代理池（如https://github.com/jhao104/proxy_pool），封装成独立服务
 - 重构为多线程爬取