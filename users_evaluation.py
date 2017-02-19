#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
import sys

class UsersEvaluation:
    users_eval = None

    # 出力ファイルにおける各カラム名
    __SCREEN_NAME = 'screen_name'
    __IS_KEYWORD_IN_PROFILE = 'is_keyword_in_profile'
    __INDIFFERENCE_COUNT = 'indifference_count'
    __RECENT_RELATE_TWEET_COUNT = 'recent_relate_tweet_count'
    __TOTAL_RELATE_TWEET_COUNT = 'total_relate_tweet_count'
    __RECENT_STATUS_ID = 'recent_status_id'

    # カラムの順序
    __COLUMN_NUM = {
        __SCREEN_NAME: 0,
        __IS_KEYWORD_IN_PROFILE: 1,
        __INDIFFERENCE_COUNT: 2,
        __RECENT_RELATE_TWEET_COUNT: 3,
        __TOTAL_RELATE_TWEET_COUNT: 4,
        __RECENT_STATUS_ID: 5
    }


    def __init__(self):
        return

    def __add_new_comer(self, screen_name):
        '''
        評価対象のユーザを新規登録するメソッド
        :param screen_name:
        :return:
        '''
        if screen_name in self.users_eval:
            raise Exception('[%s class/%s function]: users_eval is None.'
                            % (self.__class__.__name__, sys._getframe().f_code.co_name))

        # 重複してる場合はFalse
        if screen_name in self.users_eval:
            return False

        self.users_eval[screen_name] = dict()
        for column_name, column_num in self.__COLUMN_NUM.items():
            if column_name == self.__SCREEN_NAME:
                continue
            else:
                self.users_eval[screen_name][column_name] = 0
        return True

    def read_users_file(self, user_file_path):
        '''
        指定ファイルパスのcsvファイルを読み込み、
        users_evalの変数へ格納するメソッド
        :param user_file_path:
        :return:
        '''
        if user_file_path is None:
            raise Exception('[%s class/%s function]: user_file_path is None.'
                            % (self.__class__.__name__, sys._getframe().f_code.co_name))

        f = open(user_file_path, 'r')
        reader = csv.reader(f)
        self.users_eval = dict()

        for row in reader:
            if len(self.__COLUMN_NUM) != len(row):
                break
            screen_name = row[self.__COLUMN_NUM[self.__SCREEN_NAME]]
            self.users_eval[screen_name] = dict()
            for column_name, column_num in self.__COLUMN_NUM.items():
                if column_name == self.__SCREEN_NAME:
                    continue
                self.users_eval[screen_name][column_name] = row[column_num]
        f.close()
        return

    def output_users_file(self, user_file_path):
        '''
        users_evalを指定ファイルパスへcsvファイルとして保存するメソッド
        :param user_file_path:
        :return:
        '''
        if self.users_eval is None:
            raise Exception('[%s class/%s function]: users_eval is None.'
                            % (self.__class__.__name__, sys._getframe().f_code.co_name))
        if user_file_path is None:
            raise Exception('[%s class/%s function]: user_file_path is None.'
                            % (self.__class__.__name__, sys._getframe().f_code.co_name))

        f = open(user_file_path, 'w')
        writer = csv.writer(f, lineterminator='\n')
        for screen_name, user_eval in self.users_eval.items():
            row = []
            row.append(screen_name)
            for column_name, column_num in sorted(self.__COLUMN_NUM.items(),key=lambda x: x[1]):
                if column_name == self.__SCREEN_NAME:
                    continue
                row.append(user_eval[column_name])
            writer.writerow(row)
        f.close()
        return

    def add_users(self, users):
        '''
        監視対象のユーザーを追加するメソッド
        :param users:
        :return:
        '''
        if users is None or len(users) == 0:
            raise Exception('[%s class/%s function]: users is None or empty.'
                            % (self.__class__.__name__, sys._getframe().f_code.co_name))
        count = 0
        for screen_name, user in users.items():
            # 重複はスキップ
            if screen_name in self.users_eval:
                count +=1
                continue
            self.__add_new_comer(screen_name)
        return


    def evaluate_keyword_in_profile(self, twitter_controller, keywords):
        '''
        TwitterControllerクラスオブジェクトを使用して、
        ユーザ群からプロフィールにキーワードを入力しているユーザを抽出し、
        評価配列を更新するメソッド
        :param twitter_controller:
        :param keywords:
        :return:
        '''
        if self.users_eval is None:
            raise Exception('[%s class/%s function]: users_eval is None.'
                            % (self.__class__.__name__, sys._getframe().f_code.co_name))
        if twitter_controller is None:
            raise Exception('[%s class/%s function]: twitter_controller is None.'
                            % (self.__class__.__name__, sys._getframe().f_code.co_name))
        if keywords is None or len(keywords) == 0:
            raise Exception('[%s class/%s function]: keywords is None or empty.'
                            % (self.__class__.__name__, sys._getframe().f_code.co_name))

        for screen_name, user_eval, in self.users_eval.items():
            user = twitter_controller.get_user_by_screen_name(screen_name)
            user_eval[self.__IS_KEYWORD_IN_PROFILE] = 0
            for keyword in keywords:
                if keyword in user.description:
                    user_eval[self.__IS_KEYWORD_IN_PROFILE] += 1
        return

    def update_indifference_count(self, screen_name = None, count = 0):
        '''
        ユーザの興味期間更新用メソッド
        :param screen_name:
        :param term:
        :return:
        '''
        if screen_name is None:
            raise Exception('[%s class/%s function]: screen_name is None.'
                            % (self.__class__.__name__, sys._getframe().f_code.co_name))
        if self.users_eval is None:
            raise Exception('[%s class/%s function]: users_eval is None.'
                            % (self.__class__.__name__, sys._getframe().f_code.co_name))

        # 指定screen_nameのユーザが監視対象に含まれていない場合はFalse
        if screen_name not in self.users_eval:
            return False
        #if self.__INDIFFERENCE_COUNT not in self.users_eval[screen_name]:
        #    return False
        self.users_eval[screen_name][self.__INDIFFERENCE_COUNT] = count
        return True

    def update_recent_status_id(self, screen_name, tweets):
        '''
        監視対象のユーザーの最新ツイートのstatus_idを更新するメソッド
        :param screen_name:
        :param tweets:
        :return:
        '''
        if screen_name is None:
            raise Exception('[%s class/%s function]: screen_name is None.'
                            % (self.__class__.__name__, sys._getframe().f_code.co_name))
        if tweets is None or len(tweets) == 0:
            raise Exception('[%s class/%s function]: tweets is None or empty.'
                            % (self.__class__.__name__, sys._getframe().f_code.co_name))

        self.users_eval[screen_name][self.__RECENT_STATUS_ID] = tweets[0].id_str
        return

    def update_relate_tweet_count(self, screen_name, count):
        '''
        関連ツイート数、更新用メソッド
        スクリプト実行時に検出した関連ツイート数と
        合計関連ツイート数を更新する
        :param screen_name:
        :param term:
        :return:
        '''
        if self.users_eval is None:
            raise Exception('[%s class/%s function]: users_eval is None.'
                            % (self.__class__.__name__, sys._getframe().f_code.co_name))
        if screen_name is None:
            raise Exception('[%s class/%s function]: screen_name is None.'
                            % (self.__class__.__name__, sys._getframe().f_code.co_name))
        if count is None:
            raise Exception('[%s class/%s function]: count is None.'
                            % (self.__class__.__name__, sys._getframe().f_code.co_name))


        # ユーザーが監視対象に登録されていない場合は更新できないのでFalse
        if screen_name not in self.users_eval:
            return False
        #if self.__INDIFFERENCE_COUNT not in self.users_eval[screen_name]:
        #    return False

        self.users_eval[screen_name][self.__RECENT_RELATE_TWEET_COUNT] = count

        # 配列の値、すべて文字列なのでintへ変換
        total_count = int(self.users_eval[screen_name][self.__TOTAL_RELATE_TWEET_COUNT])

        self.users_eval[screen_name][self.__TOTAL_RELATE_TWEET_COUNT] = total_count + count
        return True

    def remove_indifferent_user(self, screen_name, indifference_count):
        '''
        無関心なユーザーを除外するメソッド
        指定したindifference_countと同値のユーザーを削除
        :param screen_name:
        :param indifference_count:
        :return:
        '''
        if self.users_eval is None:
            raise Exception('[%s class/%s function]: users_eval is None.'
                            % (self.__class__.__name__, sys._getframe().f_code.co_name))
        if self.users_eval[screen_name][self.__INDIFFERENCE_COUNT] == indifference_count:
            del self.users_eval[screen_name]
        return True

    def remove_user(self, screen_name):
        '''
        screen_nameからユーザーを監視対象から除外するメソッド
        :param screen_name:
        :return:
        '''
        if screen_name not in self.users_eval:
            return False
        del self.users_eval[screen_name]
        return True
