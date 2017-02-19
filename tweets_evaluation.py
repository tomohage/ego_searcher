#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
from pytz import timezone
import pytz
from datetime import datetime
import sys

class TweetsEvaluation:

    # tweets_eval[screen_name][status_id] = {favorite_count, retweet_count, relate_support_rate}
    tweets_eval = None

    twitter_controller = None

    __SCREEN_NAME = 'screen_name'
    __STATUS_ID = 'status_id'
    __FAVORITE_COUNT = 'favorite_count'
    __RETWEET_COUNT = 'retweet_count'
    __CREATED_AT = 'created_at'
    __RELATE_SUPPORTER_RATE = 'relate_supporter_rate' #関連ユーザからの支持率

    __COLUMN_NUM = {
        __SCREEN_NAME: 0,
        __STATUS_ID: 1,
        __FAVORITE_COUNT: 2,
        __RETWEET_COUNT: 3,
        __CREATED_AT: 4,
        __RELATE_SUPPORTER_RATE: 5,
    }

    def __init__(self, twitter_controller):
        self.tweets_eval = dict()
        self.twitter_controller = twitter_controller
        return

    def add_tweet(self, tweet):
        '''
        監視対象のツイートを加えるメソッド
        ツイートのstatus_idが重複してたらFalse
        追加できたらTrue
        :param tweet:
        :return:
        '''
        if self.tweets_eval is None:
            raise Exception('[%s class/%s function]: tweets_eval is None.'
                            % (self.__class__.__name__, sys._getframe().f_code.co_name))
        if tweet is None:
            raise Exception('[%s class/%s function]: tweet is None.'
                            % (self.__class__.__name__, sys._getframe().f_code.co_name))

        # 同じステータスIDのツイートがあれば追加しない
        #if tweet.id_str in self.tweets_eval:
        #    return False

        screen_name = tweet.user.screen_name
        status_id = tweet.id_str

        # screen_nameが登録されてない場合は新規追加
        if screen_name not in self.tweets_eval:
            self.tweets_eval[screen_name] = dict()

        # すでにstatus_idが登録されているツイートなら重複になるので、登録せずに終了
        if status_id in self.tweets_eval[screen_name]:
            return False

        created_at = pytz.utc.localize(tweet.created_at).astimezone(timezone('Asia/Tokyo'))
        self.tweets_eval[screen_name][status_id] = {
            self.__RETWEET_COUNT: tweet.retweet_count,
            self.__FAVORITE_COUNT: tweet.favorite_count,
            self.__CREATED_AT: created_at,
            self.__RELATE_SUPPORTER_RATE: 0
        }
        return True

    def evaluate_tweet_by_supporters_and_keywords(self, keywords):
        '''
        キーワードを用いて、ファボ,リツイートで支持しているユーザを評価するメソッド
        現状リツイートを行う支持者のみを対象とする。
        :param keywords: list型
        :return:
        '''
        if self.tweets_eval is None:
            raise Exception('[%s class/%s function]: tweets_eval is None.'
                            % (self.__class__.__name__, sys._getframe().f_code.co_name))
        if self.twitter_controller is None:
            raise Exception('[%s class/%s function]: twitter_controller is None.'
                            % (self.__class__.__name__, sys._getframe().f_code.co_name))

        for screen_name, tweet_data in self.tweets_eval.items():
            for status_id, detail in tweet_data.items():
                retweet_count = int(detail[self.__RETWEET_COUNT])
                if retweet_count == 0:
                    # リツイートされてないツイートは支持率0%
                    relate_supporter_rate = 0
                else:
                    # ツイートのstatus_idからリツイートしたユーザーのIDリストを取得
                    retweet_user_ids = self.twitter_controller.get_retweeter_from_status_id(status_id=status_id)
                    # リツイートした支持ユーザーの中からキーワードをプロフィールに含めているユーザーを抽出し、
                    # キーワードに関連する支持者がリツイートユーザの何割を占めているかを算出
                    relate_supporter_count = 0
                    total_supporter_count = len(retweet_user_ids)
                    for retweet_user_id in retweet_user_ids:
                        user = self.twitter_controller.get_user_by_user_id(retweet_user_id)
                        if self.is_keyword_in_user_profile(user=user, keywords=keywords):
                            relate_supporter_count += 1
                    relate_supporter_rate = relate_supporter_count / total_supporter_count
                self.tweets_eval[screen_name][status_id][self.__RELATE_SUPPORTER_RATE] = relate_supporter_rate
        return


    def is_keyword_in_user_profile(self, user = None, keywords = None):
        '''
        ユーザのプロフィールの中にキーワードが含まれているかどうか判定するメソッド
        :param user:
        :param keywords:
        :return:
        '''
        if keywords is None:
            raise Exception('[%s class/%s function]: keywords is None.'
                            % (self.__class__.__name__, sys._getframe().f_code.co_name))
        if user is None:
            raise Exception('[%s class/%s function]: user is None.'
                            % (self.__class__.__name__, sys._getframe().f_code.co_name))
        for keyword in keywords:
            if keyword in user.description:
                return True
        return False

    def output_tweet_file(self, tweet_file_path):
        '''
        users_evalを指定ファイルパスへcsvファイルとして保存するメソッド
        :param user_file_path:
        :return:
        '''
        if self.tweets_eval is None:
            raise Exception('[%s class/%s function]: user_eval is None.'
                            %(self.__class__.__name__, sys._getframe().f_code.co_name))
        f = open(tweet_file_path, 'w')
        writer = csv.writer(f, lineterminator='\n')
        for screen_name, tweet_eval in self.tweets_eval.items():
            for status_id, eval in tweet_eval.items():
                row = []
                row.append(screen_name)
                row.append(status_id)
                for column_name, value in sorted(self.__COLUMN_NUM.items(),key=lambda x: x[1]):
                    if column_name == self.__SCREEN_NAME:
                        continue
                    elif column_name == self.__STATUS_ID:
                        continue
                    else:
                        row.append(eval[column_name])
                writer.writerow(row)
        f.close()
        return

    def read_tweet_file(self, tweet_file_path):
        '''
        ツイートの評価用ファイルを読み込むメソッド
        :param tweet_file_path:
        :return:
        '''
        if self.tweets_eval is None:
            raise Exception('[%s class/%s function]: user_eval is None.'
                            %(self.__class__.__name__, sys._getframe().f_code.co_name))

        if tweet_file_path is None:
            raise Exception('[%s class/%s function]: tweet_file_path is None.'
                            % (self.__class__.__name__, sys._getframe().f_code.co_name))

        f = open(tweet_file_path, 'r')
        reader = csv.reader(f)
        self.tweets_eval = dict()

        for row in reader:
            if len(self.__COLUMN_NUM) != len(row):
                break
            screen_name = row[self.__COLUMN_NUM[self.__SCREEN_NAME]]
            status_id = row[self.__COLUMN_NUM[self.__STATUS_ID]]

            if screen_name not in self.tweets_eval:
                self.tweets_eval[screen_name] = dict()
            if status_id not in self.tweets_eval[screen_name]:
                self.tweets_eval[screen_name][status_id] = dict()

            for column_name, column_num in self.__COLUMN_NUM.items():
                if column_name == self.__SCREEN_NAME or column_name == self.__STATUS_ID:
                    continue
                self.tweets_eval[screen_name][status_id][column_name] = row[column_num]
        f.close()
        return

    def remove_old_and_not_attention_tweets(self, limit_date = None, max_limit_date = None):
        '''
        監視対象のツイート群から古いツイートやリツイートされていないツイートを削除するメソッド
        リツイートされていないツイートはlimit_dateを過ぎてしまうと削除され、
        リツイートされたツイートは最大max_limit_dateまで保存され、過ぎたら強制的に削除する
        :param limit_date:
        :param max_limit_date:
        :return:
        '''
        if self.tweets_eval is None:
            raise Exception('[%s class/%s function]: user_eval is None.'
                            %(self.__class__.__name__, sys._getframe().f_code.co_name))
        if limit_date is None:
            raise Exception('[%s class/%s function]: limit_date is None.'
                            % (self.__class__.__name__, sys._getframe().f_code.co_name))
        if max_limit_date is None:
            raise Exception('[%s class/%s function]: max_limit_date is None.'
                            % (self.__class__.__name__, sys._getframe().f_code.co_name))

        for screen_name, tweets in self.tweets_eval.items():
            for status_id, eval in tweets.items():
                if type(eval[self.__CREATED_AT]) is str:
                    created_at = datetime.strptime(eval[self.__CREATED_AT], '%Y-%m-%d %H:%M:%S+09:00')
                    created_at = timezone('Asia/Tokyo').localize(created_at)
                else:
                    created_at = eval[self.__CREATED_AT]
                retweet_count = int(eval[self.__RETWEET_COUNT])
                if (created_at < limit_date and retweet_count == 0) or created_at < max_limit_date:
                    del self.tweets_eval[screen_name][status_id]
        return True

    def convert_tweet_eval_to_ranking_data(self):
        '''
        tweet_evalをランキング用のdictへ変換して返すメソッド
        このメソッドでは以下の式で評価スコアをつけている
        評価ストア = (リツイート数+ファボ数) * 関連ユーザーの支持率
        :return:
        '''
        if self.tweets_eval is None:
            raise Exception('[%s class/%s function]: user_eval is None.'
                            %(self.__class__.__name__, sys._getframe().f_code.co_name))

        ranking_data = dict()
        for screen_name, tweet_eval in self.tweets_eval.items():
            for status_id, eval in tweet_eval.items():
                retweet_count = int(eval[self.__RETWEET_COUNT])
                favorite_count = int(eval[self.__FAVORITE_COUNT])
                relate_supporter_rate = float(eval[self.__RELATE_SUPPORTER_RATE])
                ranking_data[status_id] = (retweet_count + favorite_count) * (1 + relate_supporter_rate)
        return ranking_data


