#!/usr/bin/env python
# -*- coding: utf-8 -*-
from twitter_controller import TwitterController
from tweets_evaluation import TweetsEvaluation

from users_evaluation import UsersEvaluation
from datetime import datetime, timedelta
from pytz import timezone
from janome.tokenizer import Tokenizer
import pytz, re, sys, traceback

_CONSUME_KEY = 'l8KlRcAt0CR3gcZCpqrGZRHx9'
_CONSUME_SECRET = 'qlgvVexVvJeyujSPbYzuffBHYGxH7d3bcvYxhRriWMnMb54cpJ'
_ACCESS_TOKEN = '829332236608483329-zex5aXl0CJRQGXAKZ4X5IX9LplvzdQ4'
_ACCESS_TOKEN_SECRET = 'SeazoxLOu3BkOBZMbyNCapweeFWIVsIbXWhmpplicUi3U'

_USER_FILE_PATH = '/Users/tomoki/workspace/tweepy_test/user_data/users.csv'
_TWEET_FILE_PATH = '/Users/tomoki/workspace/tweepy_test/user_data/tweet.csv'

_KEYWORDS = [u'消滅都市', u'都市ったー', u'消滅', u'マルチ']

_NG_WORDS = [
    u'http', u'://', u'co', u'RT', u'000', u'00', u'amp', u'Twitter', u'GET', u'LINE', u'ゲーム',
    u'さん', u'ちゃん', u'開催', u'人人', u'(', u')', u'!', u':', u'_', u'リツイート', u'公式', u'･'
]


def is_ng_word(word):
    '''
    wordがNGワードに含まれていないか確認するメソッド
    :param word:
    :return:
    '''
    if word is None:
        raise Exception('[%s function]: query is None.' % sys._getframe().f_code.co_name)
    for ng_word in _NG_WORDS:
        if ng_word in word:
            return True
    return False

def get_norm_total_by_tweets(tweets):
    '''
    tweetsを形態素解析して、単語と使用回数のセットdictを作成するメソッド
    :param tweets:
    :return:
    '''
    if tweets is None or len(tweets) == 0:
        raise Exception('[%s function]: tweets is None or empty.' % sys._getframe().f_code.co_name)

    norm = dict()
    t = Tokenizer()
    if tweets is None:
        return None
    for tweet in tweets:
        tokens = t.tokenize(tweet.text)
        for token in tokens:
            surface = token.surface
            word_class = token.part_of_speech.split(',')[0]
            half_regexp = re.compile(r'^[0-9A-Za-z]+$')
            number_regexp = re.compile(r'^[0-9]+$')
            # 半角英数字で2文字以下の文字列はいれない
            if half_regexp.search(surface) and len(surface) <= 2:
                continue
            # 数値のみの文字列はいれない
            if number_regexp.search(surface):
                continue
            # NGワードを含めない
            if is_ng_word(surface):
                continue
            if word_class == u'名詞' and len(surface) > 1:
                if surface in norm:
                    norm[surface] += 1
                else:
                    norm[surface] = 1
    return norm

def user_evaluate(twitter_controller, query, until, since, limit_count, limit_indifference_count):
    '''
    ユーザを評価するメソッド
    :param twitter_controller:
    :param until:
    :param since:
    :param limit_count:
    :param limit_indifference_count:
    :return:
    '''
    # 既に保存しているユーザを読み込み評価オブジェクトへ保存
    users_eval = UsersEvaluation()
    users_eval.read_users_file(_USER_FILE_PATH)

    # クエリ通りのツイートしたユーザを抽出し、評価オブジェクトへ追加
    new_users = twitter_controller.get_users_tweet_query(query, count = limit_count)
    users_eval.add_users(new_users)

    # プロフィールにキーワードが含まれているユーザを抽出して評価
    users_eval.evaluate_keyword_in_profile(tc, _KEYWORDS)

    # 公式アカウントのツイートを取得し、形態素解析する
    # それっぽい単語とその単語の使用回数を取得
    official_tweets = twitter_controller.get_tweets_by_screen_name(u'shoumetsutoshi',
                                                                   count = limit_count, exclude_replies = True)
    relate_norms = get_norm_total_by_tweets(official_tweets)

    # 形態素解析した単語のうち、使用頻度の高い単語をピックアップ
    freq_relate_norms = dict()
    for relate_norm, count in sorted(relate_norms.items(), key = lambda x: x[1], reverse = True):
        if count > 1:
            freq_relate_norms[relate_norm] = count

    # 監視対象のユーザーが直近に投稿したツイートのうち、
    # 公式アカウントが使用する汎用単語を含んだツイートを抽出し、ユーザ毎に集計を行う
    for screen_name, user_eval in users_eval.users_eval.items():
        # 前の処理の時間を考慮して現在時刻を取得し直す
        tweets = twitter_controller.get_tweets_by_screen_name(screen_name,
                                                              count = limit_count,
                                                              since = since, until = until,
                                                              exclude_replies = False)

        # 検索結果のツイートのうち、公式アカウントの汎用単語を使用しているツイートを集める
        # 前回の集計で調べたツイートまで最大遡る
        relate_tweet_count = 0
        for tweet in tweets:
            # 前回の最新ツイートまで遡ったらbreak
            if tweet.id_str == users_eval.users_eval[screen_name]['recent_status_id']:
                break
            user_relate_norms = get_norm_total_by_tweets([tweet])
            relate_norm_count = 0
            for user_relate_norm, count in user_relate_norms.items():
                if user_relate_norm in freq_relate_norms:
                    relate_norm_count += 1
            if relate_norm_count > 0:
                relate_tweet_count += 1

        # 評価オブジェクトに関連ツイートの数を設定/加算
        users_eval.update_relate_tweet_count(screen_name, count = relate_tweet_count)

        # 評価オブジェクト内の最新ツイートのIDを更新
        # ツイートがなければ更新しない
        if len(tweets) > 0:
            users_eval.update_recent_status_id(screen_name, tweets)

        # 関連ツイートが見つからなかった場合、無関心カウントを1増やし、
        # もし無関心カウントが上限値を迎えた場合、監視ユーザの対象方はずす
        # 関連ツイートが発見された場合、無関心カウントを0にする
        if relate_tweet_count > 0:
            users_eval.update_indifference_count(screen_name, count = 0)
        else:
            indifference_count = int(users_eval.users_eval[screen_name]['indifference_count']) + 1
            users_eval.update_indifference_count(screen_name, count = indifference_count)
            if indifference_count == limit_indifference_count:
                users_eval.remove_user(screen_name)
    # csvファイルに保存
    users_eval.output_users_file(_USER_FILE_PATH)

def tweet_evaluate(twitter_controller, until, since, limit_tweet_count):
    '''
    監視対象のツイートを更新し、ツイートを評価するメソッド
    :param twitter_controller:
    :param until:
    :param since:
    :param limit_tweet_count:
    :return:
    '''
    ue = UsersEvaluation()
    ue.read_users_file(_USER_FILE_PATH)

    # TweetsEvaluationクラスでツイート評価用ファイルを読み込む
    te = TweetsEvaluation(tc)
    te.read_tweet_file(_TWEET_FILE_PATH)

    # 監視対象のユーザの新しいツイートを評価オブジェクトへ追加
    for screen_name, user_eval in ue.users_eval.items():
        tweets = twitter_controller.get_tweets_by_screen_name(screen_name, count = limit_tweet_count,
                                                              since = since, until = until,
                                                              exclude_replies = False)
        for tweet in tweets:
            te.add_tweet(tweet)

    # ツイートのリツイート数、ふぁぼ数を更新し、
    # リツイートしているユーザーのうち、キーワードを含んだプロフィールを持つユーザーの割合を算出
    te.evaluate_tweet_by_supporters_and_keywords(_KEYWORDS)

    # リツイートされていないツイートはlimit_dateを過ぎると監視対象からはずし、
    # リツイートされているツイートはmax_limit_dateを過ぎると監視対象からはずれる
    limit_date = datetime.now(pytz.timezone('Asia/Tokyo')) - timedelta(hours=1)
    max_limit_date = datetime.now(pytz.timezone('Asia/Tokyo')) - timedelta(days=1)

    # 古いツイートやリツイートされていないツイートは監視対象からはずす
    te.remove_old_and_not_attention_tweets(limit_date, max_limit_date)

    # ファイルに保存する
    te.output_tweet_file(_TWEET_FILE_PATH)

def create_attention_ranking(twitter_controller, best = 10):
    # TweetsEvaluationクラスでツイート評価用ファイルを読み込む
    te = TweetsEvaluation(tc)
    te.read_tweet_file(_TWEET_FILE_PATH)
    ranking = te.convert_tweet_eval_to_ranking_data()

    count = 1
    print '------------------------------------------------'
    for status_id, score in sorted(ranking.items(), key=lambda x: x[1], reverse = True):
        tweet = twitter_controller.get_tweet_by_status_id(status_id)
        created_at = pytz.utc.localize(tweet.created_at).astimezone(timezone('Asia/Tokyo'))
        print '%s位: %s' %(str(count), str(score))
        print '投稿日: ' + created_at.strftime('%Y-%m-%d %H:%M:%S')
        print 'ファボ数: ' + str(tweet.favorite_count)
        print 'リツイート数: ' + str(tweet.retweet_count)
        print '本文: ' + tweet.text
        url = 'https://twitter.com/' + tweet.user.screen_name + '/status/' + tweet.id_str
        print 'URL: ' + url
        print '------------------------------------------------'
        count += 1
        if count > best:
            break

if __name__ == "__main__":
    try:
        tc = TwitterController(_CONSUME_KEY, _CONSUME_SECRET, _ACCESS_TOKEN, _ACCESS_TOKEN_SECRET)
        # 無関心時間
        # この期間を過ぎてもキーワードを呟かないユーザは
        # 興味がなくなったと見做して監視対象からはずす
        indifference_minutes = 3 * 24 * 60
        script_interval_minutes = 10

        # ユーザ評価の際、取得するツイートの上限数
        limit_tweet_count = 100

        # スクリプトを実行し続けてlimit_indifference_count回無関心だった場合、監視対象からはずす
        limit_indifference_count = indifference_minutes / script_interval_minutes

        # datetimeオブジェクをawareで取得する
        # 念のためにsinceは+5分くらい拡張
        until = datetime.now(pytz.timezone('Asia/Tokyo'))
        since = until - timedelta(minutes=script_interval_minutes + 5)
        query = u"消滅都市 OR #消滅都市 " \
                u"-\"消滅可能性都市\" -\"データ販売\" " \
                u"since:" + since.strftime('%Y-%m-%d_%H:%M:%S_JST') + u" " + \
                u"until:" + until.strftime('%Y-%m-%d_%H:%M:%S_JST')+ u" " + \
                u"exclude:retweets"
        print '------------------------------------------------------'
        print datetime.now().strftime('%Y-%m-%d_%H:%M:%S_JST') + ': ユーザー評価監視システム実行開始'
        user_evaluate(tc, query, until, since, limit_tweet_count, limit_indifference_count)
        print datetime.now().strftime('%Y-%m-%d_%H:%M:%S_JST') + ': ユーザー評価監視システム実行終了'

        print datetime.now().strftime('%Y-%m-%d_%H:%M:%S_JST') + ': ツイート評価システム実行開始'
        tweet_evaluate(tc, until, since, limit_tweet_count)
        print datetime.now().strftime('%Y-%m-%d_%H:%M:%S_JST') + ': ツイート評価システム実行終了'
        create_attention_ranking(tc)
        print '------------------------------------------------------'
    except Exception as e:
        print type(e)
        print e
        tbinfo = traceback.format_tb(sys.exc_info()[2])
        for tbi in tbinfo:
            print tbi

