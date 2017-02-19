#!/usr/bin/env python
# -*- coding: utf-8 -*-
import tweepy
from pytz import timezone
import pytz, sys
import time


class TwitterController:
    __API = None
    __AUTH = None
    __MAX_GETTABLE_TWEETS_NUM = 100

    def __init__(self, consumer_key, consumer_secret, access_token, access_token_secret):
        self.__AUTH = tweepy.OAuthHandler(consumer_key, consumer_secret)
        self.__AUTH.set_access_token(access_token, access_token_secret)
        self.__API = tweepy.API(self.__AUTH)


    def clear(self):
        self.__API = None
        self.__AUTH = None

    def tweet(self, body):
        '''
        ツイートする
        :param body:
        :return:
        '''
        if self.__API is None:
            raise Exception('[%s class/%s function]: API is None.'
                            % (self.__class__.__name__, sys._getframe().f_code.co_name))
        if body is None:
            raise Exception('[%s class/%s function]: body is None.'
                            % (self.__class__.__name__, sys._getframe().f_code.co_name))

        self.__API.update_status(body)
        return True

    def get_tweet_by_query(self, query, count, display=False):
        """
        クエリ通りの条件で検索し指定件数分のツイートを出力するメソッド
        クエリはtwitterの仕様通りです。
        参考:
        http://so-zou.jp/web-app/tech/web-api/twitter/search/search-query.htm
        http://s-supporter.hatenablog.jp/entry/twitter-search-criteria
        :param query:
        :param count:
        :return:
        """
        if self.__API is None:
            raise Exception('[%s class/%s function]: API is None.'
                            % (self.__class__.__name__, sys._getframe().f_code.co_name))
        if query is None:
            raise Exception('[%s class/%s function]: query is None.'
                            % (self.__class__.__name__, sys._getframe().f_code.co_name))
        if count is None:
            raise Exception('[%s class/%s function]: count is None.'
                            % (self.__class__.__name__, sys._getframe().f_code.co_name))

        c = tweepy.Cursor(self.__API.search, q=query, include_entities=True, result_type='recent').items()
        tweet_count = 0
        tweets = []
        while tweet_count < count:
            try:
                tweet = c.next()
                tweet_count += 1
                if display:
                    print '------------------------------------------------------'
                    print '【' + tweet_count.__str__() + 'ツイート目】'
                    self.__print_tweet(tweet)
                tweets.append(tweet)
            except tweepy.TweepError:
                print 'start break time _(:3｣∠)_'
                time.sleep(60 * 15)
                print 'break time is over _(┐「ε:)_'
                continue
            except StopIteration:
                break
        return tweets

    @staticmethod
    def __print_tweet(tweet):
        print '投稿日: ' + tweet.created_at.strftime('%Y-%m-%d %H:%M:%S')
        print 'ファボ数: ' + str(tweet.favorite_count)
        print 'リツイート数: ' + str(tweet.retweet_count)
        print u'本文: ' + tweet.text
        url = 'https://twitter.com/' + tweet.user.screen_name + '/status/' + tweet.id_str
        print 'URL: ' + url

    def get_users_tweet_query(self, query, count = 100):
        '''
        検索クエリを発行して取得したツイートを投稿したユーザを取得し、
        配列にまとめて返すメソッド（keyはscreen_name）
        countでツイートの上限数を指定
        :param query:
        :param count:
        :return:
        '''
        if self.__API is None:
            raise Exception('[%s class/%s function]: API is None.'
                            % (self.__class__.__name__, sys._getframe().f_code.co_name))
        if query is None:
            raise Exception('[%s class/%s function]: query is None.'
                            % (self.__class__.__name__, sys._getframe().f_code.co_name))
        if count is None:
            raise Exception('[%s class/%s function]: count is None.'
                            % (self.__class__.__name__, sys._getframe().f_code.co_name))

        tweets = self.get_tweet_by_query(query, count, display=False)
        users = dict()
        for tweet in tweets:
            # ダブりユーザは排除
            screen_name = tweet.user.screen_name
            if screen_name not in users:
                users[screen_name] = self.__API.get_user(id=screen_name)
        return users

    def get_user_by_screen_name(self, screen_name):
        '''
        screen_nameからtwitterのユーザオブジェクトを取得して返すメソッド
        :param screen_name:
        :return:
        '''
        if self.__API is None:
            raise Exception('[%s class/%s function]: API is None.'
                            % (self.__class__.__name__, sys._getframe().f_code.co_name))
        if screen_name is None:
            raise Exception('[%s class/%s function]: screen_name is None.'
                            % (self.__class__.__name__, sys._getframe().f_code.co_name))

        return self.__API.get_user(id=screen_name)

    def get_tweets_by_screen_name(self, screen_name, count = 100, since = None, until = None, exclude_replies = False):
        '''
        screen_nameから該当ユーザのツイートを取得するメソッド
        取得するツイートは新しいものから順
        取得ツイートはsinceからuntilまでの期間
        :param screen_name:
        :param count: 取得数
        :param since: datetimeオブジェクト
        :param until: datetimeオブジェクト
        :return:
        '''
        if self.__API is None:
            raise Exception('[%s class/%s function]: API is None.'
                            % (self.__class__.__name__, sys._getframe().f_code.co_name))
        if screen_name is None:
            raise Exception('[%s class/%s function]: screen_name is None.'
                            % (self.__class__.__name__, sys._getframe().f_code.co_name))

        tweets = []
        c = tweepy.Cursor(self.__API.user_timeline,
                          screen_name=screen_name,
                          count=count,
                          exclude_replies = exclude_replies,
                          include_rts = False).items()
        tweet_count = 0
        while tweet_count < count:
            try:
                # TwitterAPIとしては最新のツイートから順に取得される
                tweet = c.next()
                created_at = pytz.utc.localize(tweet.created_at).astimezone(timezone('Asia/Tokyo'))
                # ツイート日時が指定期間より未来ならappendしない
                if until:
                    if created_at > until:
                        continue
                # ツイート日時が指定期間より過去なら取得終了
                if since:
                    if created_at < since:
                        break
                tweet_count += 1
                tweets.append(tweet)
            except tweepy.TweepError:
                print 'start break time _(:3｣∠)_'
                time.sleep(60 * 15)
                print 'break time is over _(┐「ε:)_'
                continue
            except StopIteration:
                break
        return tweets

    def get_users_by_keywords(self, query, count = 100, include_protected=False):
        '''
        キーワードを含んだプロフィールをもつユーザーを取得するメソッド
        :param query:
        :param count:
        :param include_protected:
        :return:
        '''
        # TODO: ユーザ検索時のユーザのソートができない。最終ツイートの日付順とかクエリで設定できれば最高です。
        if self.__API is None:
            raise Exception('[%s class/%s function]: API is None.'
                            % (self.__class__.__name__, sys._getframe().f_code.co_name))
        if query is None:
            raise Exception('[%s class/%s function]: query is None.'
                            % (self.__class__.__name__, sys._getframe().f_code.co_name))
        if count is None:
            raise Exception('[%s class/%s function]: count is None.'
                            % (self.__class__.__name__, sys._getframe().f_code.co_name))

        c = tweepy.Cursor(self.__API.search_users, count=count, q=query, result_type='recent').items()
        user_count = 0
        users = []
        while user_count < count:
            try:
                user = c.next()
                user_count += 1
                if include_protected is False and user.protected:
                    continue
                users.append(user)
            except tweepy.TweepError:
                print 'start break time _(:3｣∠)_'
                time.sleep(60 * 15)
                print 'break time is over _(┐「ε:)_'
                continue
            except StopIteration:
                break
        return users

    def get_retweeter_from_status_id(self, status_id):
        '''
        status_idが示すツイートをリツイートしているユーザーを取得するメソッド
        :param status_id:
        :return:
        '''
        if self.__API is None:
            raise Exception('[%s class/%s function]: API is None.'
                            % (self.__class__.__name__, sys._getframe().f_code.co_name))
        if status_id is None:
            raise Exception('[%s class/%s function]: status_id is None.'
                            % (self.__class__.__name__, sys._getframe().f_code.co_name))

        return self.__API.retweeters(id=status_id)

    def get_user_by_user_id(self, user_id):
        '''
        user_idからユーザーを取得するメソッド
        :param user_id:
        :return:
        '''
        if self.__API is None:
            raise Exception('[%s class/%s function]: API is None.'
                            % (self.__class__.__name__, sys._getframe().f_code.co_name))

        if user_id is None:
            raise Exception('[%s class/%s function]: user_id is None.'
                            % (self.__class__.__name__, sys._getframe().f_code.co_name))

        return self.__API.get_user(user_id)

    def get_tweet_by_status_id(self, status_id):
        return self.__API.get_status(id=status_id)

    def get_favoriter_from_status_id(self, status_id):
        '''
        ツイートをファボったユーザを取得するメソッド
        :param status_id:
        :return:
        '''
        # TODO:ファボったユーザ情報とれないんで調査していずれ実装する。とりまRTユーザのみで
        if status_id is None:
            return False
        self.__API.search()




