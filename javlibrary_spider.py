#-*- coding: UTF-8 -*- 
import scrapy
import string
import logging
import math
import random
from javlibrary.artistitem import ArtistItem
from javlibrary.europeartistitem import EuropeArtistItem
from javlibrary.filmitem import FilmItem
from javlibrary.genreitem import GenreItem
from javlibrary.db import db
from javlibrary.db.artist import Artist
from javlibrary.db.film import Film
from scrapy import log

class ArtistSpider(scrapy.Spider):
    name = 'Artist'
    allowed_domians = ['javbus.info']
    base_url = 'https://www.javbus.info/'
    start_urls = [ base_url+'actresses/1']
    def parse(self, response):
        nextpage = u'下一頁'
        for href in response.xpath('//ul[contains(@class,"pagination")]/li/a[contains(text(),"%s")]'%(nextpage)).css('a::attr("href")'):
            url = response.urljoin(href.extract())
            yield scrapy.Request(url, callback=self.parse)
        for artist in response.xpath('//div[@class="item"]'):
            artistItem = ArtistItem()
            artistItem['name'] = artist.xpath('.//div[@class="photo-info"]/span/text()').extract()[0].encode('utf-8')
            artistItem['url'] = artist.xpath('.//a/@href').extract()[0].encode('utf-8').replace('https://www.javbus.info/','')
            artistItem['stag'] = artistItem['url'].split('/')[-1]
            yield artistItem

class EuropeArtistSpider(scrapy.Spider):
    name = 'EuropeArtist'
    allowed_domians = ['javbus.xyz']
    base_url = 'https://www.javbus.xyz/'
    start_urls = [ base_url+'actresses/1']
    def parse(self, response):
        nextpage = u'下一頁'
        for href in response.xpath('//ul[contains(@class,"pagination")]/li/a[contains(text(),"%s")]'%(nextpage)).css('a::attr("href")'):
            url = response.urljoin(href.extract())
            yield scrapy.Request(url, callback=self.parse)
        for artist in response.xpath('//div[@class="item"]'):
            artistItem = EuropeArtistItem()
            artistItem['name'] = artist.xpath('.//div[@class="photo-info"]/span/text()').extract()[0].encode('utf-8')
            artistItem['url'] = artist.xpath('.//a/@href').extract()[0].encode('utf-8').replace('https://www.javbus.xyz/','')
            artistItem['stag'] = artistItem['url'].split('/')[-1]
            yield artistItem


class TopArtistSpider(scrapy.Spider):
    name = 'TopArtist'
    allowed_domians = ['ja7lib.com']
    start_urls = [
            'http://ja7lib.com/cn/star_mostfav.php'
            ]

    def parse(self, response):
        for artist in response.xpath('//div[@class="searchitem"]'):
            artistItem = ArtistItem()
            artistItem['name'] = artist.css('img::attr("title")').extract()[0].encode('utf-8')
            artistItem['stag'] = artist.css('div::attr("id")').extract()[0].encode('utf-8')
            artistItem['url'] = artist.css('a::attr("href")').extract()[0].encode('utf-8')
            artistItem['img'] = artist.css('img::attr("src")').extract()[0].encode('utf-8')
            artistItem['rank'] = int(artist.re('#(\d+) ')[0].encode('utf-8'))
            yield artistItem

class GenreSpider(scrapy.Spider):
    name = 'Genre'
    allowed_domians = ['javbus.info']
    start_urls = [
            'https://www.javbus.info/genre/'
            ]

    def parse(self, response):
        for genre in response.xpath("//a[contains(@href,'https://www.javbus.info/genre/')]"):
            genreItem = GenreItem()
            genreItem['name'] = genre.xpath('./text()').extract()[0].encode('utf-8')
            genreItem['url'] = genre.xpath('./@href').extract()[0].encode('utf-8')
            yield genreItem


class FilmSpider(scrapy.Spider):
    name = 'Film'
    allowed_domians = ['javbus.info']
    base_url = 'https://www.javbus.info/'
    session = db.getsession()
    start_urls = [ base_url + result.url for result in session.query(Artist.url).filter(Artist.aid==3).all() ]
    session.close()

    def parse(self, response):
        for href in response.xpath('//a[@class="movie-box"]').css('a::attr(href)'):
            url = response.urljoin(href.extract())
            yield scrapy.Request(url, callback=self.parse_one_film)
        nextpage = u'下一頁'
        for href in response.xpath('//ul[contains(@class,"pagination")]/li/a[contains(text(),"%s")]'%(nextpage)).css('a::attr("href")'):
            url = response.urljoin(href.extract())
            yield scrapy.Request(url, callback=self.parse)

    def parse_one_film(self, response):
        film = FilmItem()
        code=u'識別碼:'
        film['id'] = response.xpath("//p[contains(., '%s')]//text()"%(code)).extract()[-1].encode('utf-8')
        film['name'] = self.getstring(response.xpath("//h3//text()"))
        film['cover'] = self.getstring(response.xpath("//a[@class='bigImage']/@href"))
        pubdate=u'發行日期:'
        film['date'] = response.xpath("//p[contains(., '%s')]//text()"%(pubdate)).extract()[-1].encode('utf-8')
        vlengt=u'長度:'
        film['length'] = response.xpath("//p[contains(., '%s')]//text()"%(vlengt)).extract()[-1].encode('utf-8')
        film['director'] = ''
        
        productor=u'製作商:'
        film['maker'] = response.xpath("//p[contains(., '%s')]//text()"%(productor)).extract()[-1].encode('utf-8')
        publisher=u'發行商:'
        film['producer'] = response.xpath("//p[contains(., '%s')]//text()"%(publisher)).extract()[-1].encode('utf-8')
        film['producer_url'] = response.xpath("//p[contains(., '%s')]/a/@href"%(publisher)).extract()[-1].encode('utf-8')
        series=u'系列:'
        arrSeries=response.xpath("//p[contains(., '%s')]//text()"%(series)).extract()
        series_url=response.xpath("//p[contains(., '%s')]/a/@href"%(series)).extract()
        if len(arrSeries)>0:
            film['series']=arrSeries[-1].encode('utf-8')
            film['series_url']=series_url[-1].encode('utf-8')
        else:
            film['series']=''
            film['series_url']=''
        arrActors=response.xpath("//div[@class='star-name']//text()").extract()
        if len(arrActors)>1:
            uactors=','.join(arrActors)
            film['actors']=uactors.encode('utf-8')
        else:
            film['actors']=arrActors[0].encode('utf-8')
            
        arrCategorys=response.xpath("//span[@class='genre']/a[contains(@href,'https://www.javbus.info/genre')]//text()").extract()
        if len(arrCategorys)>1:
            ucategorys=','.join(arrCategorys)
            film['categorys']=ucategorys.encode('utf-8')
        else:
            film['categorys']=arrCategorys[0].encode('utf-8')
        
        session = db.getsession()
        if session.query(Film).filter(Film.tag == film['id']).one_or_none() == None:    
            film['image_urls'] = response.xpath("//a[@class='bigImage']/@href").extract()
            previews=response.xpath("//div[@id='sample-waterfall']/a[@class='sample-box']/@href").extract()
            if previews:
                film['image_urls'].extend(previews)
            else:
                log.msg('no preview!   '+response.url,level=log.DEBUG)
        else:
            film['image_urls']=[]
        session.close()
        film['score']=0
        film['category'] = [ gen.extract().encode('utf-8') for gen in response.xpath("//span[@class='genre']/a[contains(@href,'https://www.javbus.info/genre')]//text()") ]
        film['cast'] = [star.extract().encode('utf-8')for star in response.xpath("//div[@class='star-name']//text()")]
        film['url'] = response.url
        
        
        #添加测试
        #磁力
        strst=response.xpath("//script[contains(.,'gid')]//text()").extract()[0].encode('utf-8')
        e1=strst.index('=')
        f1=strst.index(';')
        gid=strst[e1+1:f1].strip()
        
        strst=strst[f1+1:]
        e2=strst.index('=')
        f2=strst.index(';')
        uc=strst[e2+1:f2].strip()
        
        magenReq='https://www.javbus.info/ajax/uncledatoolsbyajax.php?gid=' + gid + '&lang=zh&img=' + film['cover'] + '&uc=' + uc + '&floor=' + str(random.randint(0,1000))
        log.msg(magenReq,level=log.DEBUG)
        request = scrapy.Request(magenReq, callback=self.parse_magnet)
        request.meta['item']=film
        yield request

    def getstring(self, selector):
        if len(selector) == 0:
            return None
        else:
            return selector.extract()[0].encode('utf-8')

    def parse_magnet(self,response):
        item = response.meta['item']
        log.msg('-------------code %s and name %s '%(item['id'],item['name']),level=log.DEBUG)
        links=response.xpath("//tr")
        temp=[]
        arrMagnets=[]
        for index, link in enumerate(links):
            args =','.join([link.xpath('.//td[1]/a/text()').extract()[0].encode('utf-8').strip(), link.xpath('.//td[2]/a/text()').extract()[0].encode('utf-8').strip(),link.xpath('.//td[3]/a/text()').extract()[0].encode('utf-8').strip(),link.xpath('.//td[1]/a/@href').extract()[0].encode('utf-8').strip()])
            arrMagnet=[link.xpath('.//td[1]/a/text()').extract()[0].encode('utf-8').strip(), link.xpath('.//td[2]/a/text()').extract()[0].encode('utf-8').strip(),link.xpath('.//td[3]/a/text()').extract()[0].encode('utf-8').strip(),link.xpath('.//td[1]/a/@href').extract()[0].encode('utf-8').strip()]
            temp.append(args)
            arrMagnets.append(arrMagnet)
        strMagnet=','.join(temp)
        item['arrmagnet']=arrMagnets
        item['magnet']=strMagnet
        log.msg('--------------all magnets',level=log.DEBUG)
        return item
    
