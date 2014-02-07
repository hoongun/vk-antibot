#!/usr/bin/python

import sys, getopt
import time
import vkontakte as vk

GROUP_ID = '123456'
CITY_ID = 1   # Moscow

class VKUserChecker(object):
    def __init__(self, token, filename, begin, post_id, count, offset):
        self.api = vk.API(token=token, timeout=20)
        self.begin = int(begin)
        self.post_id = int(post_id)
        self.offset = int(offset)
        self.count = int(count)
        self.file = open(filename, 'a')

    def save_info(self, line):
        self.file.write(line + '\r\n')
        self.file.flush()

    def get_city_name(self, user):
        while True:
            try:
                cities = self.api.get('database.getCitiesById', city_ids=user['city'])
            except Exception as e:
                print 'Exception City:', user['city'], e
                time.sleep(30)
                continue
            break
        if cities:
            return cities[0]['name'].encode('utf8')
        return ''

    def get_friends(self, uid):
        users = []
        offset = 0
        while True:
            friends = self.api.get('friends.get', user_id=uid, fields='city', count=1000, offset=offset)
            users += friends
            if len(friends) < 1000:
                break
            offset += 1000
            time.sleep(1)

        ulsk_friends, fail_friends = [], []
        for friend in friends:
            if 'city' not in friend or 'deactivated' in friend:
                fail_friends.append(friend)
            else:
                if int(friend['city']) == CITY_ID:
                    ulsk_friends.append(friend)
        return len(ulsk_friends), len(friends), len(fail_friends)

    def get_followers(self, uid):
        users = []
        offset = 0
        while True:
            followers = self.api.get('users.getFollowers', user_id=uid, fields='city', count=1000, offset=offset)
            count = followers['count']
            users += followers['items']
            if len(users) >= count:
                offset += 1000
                break
            time.sleep(1)

        ulsk_users, fail_users = [], []
        for user in users:
            if 'city' not in user or 'deactivated' in user:
                fail_users.append(user)
            else:
                if int(user['city']) == CITY_ID:
                    ulsk_users.append(user)
        return len(ulsk_users), len(users), len(fail_users)

    def get_user_friends(self, uid, **kwargs):
        deactivated = False
        total, real, fail = 0, 0, 0

        while True:
            try:
                total, real, fail = self.get_friends(uid)
            except Exception as e:
                print 'EXCEPT:', uid, e
                if hasattr(e, 'code') and e.code == 15:
                    # Access denied: user deactivated
                    deactivated = True
                    break
                time.sleep(30)
                continue
            break

        kwargs.update({
            'deactivated': kwargs['deactivated'] or deactivated,
            'friends': {
                'total': total,
                'real': real,
                'fail': fail
            }
        })
        return kwargs

    def get_user_followers(self, uid, **kwargs):
        deactivated = False
        total, real, fail = 0, 0, 0

        while True:
            try:
                total, real, fail = self.get_followers(uid)
            except Exception as e:
                print 'EXCEPT:', uid, e
                if hasattr(e, 'code') and e.code == 15:
                    # Access denied: user deactivated
                    deactivated = True
                    break
                time.sleep(30)
                continue
            break

        kwargs.update({
            'deactivated': kwargs['deactivated'] or deactivated,
            'followers': {
                'total': total,
                'real': real,
                'fail': fail
            }
        })
        return kwargs

    def get_user_profile(self, uid, **kwargs):
        deactivated = False
        city = ''
        photo_100, first_name, last_name = '', '', ''

        while True:
            try:
                user = self.api.get('users.get', user_ids=uid, fields='photo_100,city,first_name,last_name')[0]
            except Exception as e:
                print 'EXCEPT:', uid, e
                if hasattr(e, 'code') and e.code == 15:
                    # Access denied: user deactivated
                    deactivated = True
                    break
                time.sleep(30)
                continue
            break

        if 'deactivated' in user:
            print 'User deactivated by key'
            deactivated = True

        if kwargs['deactivated'] or deactivated:
            print 'User deactivated', user
            city = ''
            photo_100 = ''
            first_name = ''
            last_name = ''
        else:
            city = ''
            if 'city' in user:
                city = self.get_city_name(user)

            photo_100 = user['photo_100'].encode('utf8')
            first_name = user['first_name'].encode('utf8')
            last_name = user['last_name'].encode('utf8')

        kwargs.update({
            'deactivated': kwargs['deactivated'] or deactivated,
            'user': {
                'city': city,
                'photo_100': photo_100,
                'first_name': first_name,
                'last_name': last_name,
            }
        })
        return kwargs

    def get_user_group_member(self, uid, **kwargs):
        deactivated = False
        is_member = False
        while True:
            try:
                is_member = bool(self.api.get('groups.isMember', group_id=GROUP_ID, user_id=uid))
            except Exception as e:
                print 'EXCEPT:', uid, e
                if hasattr(e, 'code') and e.code == 15:
                    # Access denied: user deactivated
                    deactivated = True
                    break
                time.sleep(30)
                continue
            break

        kwargs.update({
            'deactivated': kwargs['deactivated'] or deactivated,
            'group_member': is_member
        })
        return kwargs

    def sort_out(self):
        users = self.get_user_list()

        num = self.begin
        for uid in users:
            time.sleep(1)

            num += 1

            if int(uid) < 0:
                line = '%04d) %s\t%5s\t%5s\t%5s\t%5s\t%5s\t%5s\t%s\t%s\t%s\t%s\t%s' % (
                    num,
                    uid,
                    '', '', '', '', '', '', '', '', '', '', ''
                )
            else:
                kwargs = {
                    'deactivated': False
                }

                kwargs = self.get_user_friends(uid, **kwargs)
                kwargs = self.get_user_followers(uid, **kwargs)
                kwargs = self.get_user_profile(uid, **kwargs)
                kwargs = self.get_user_group_member(uid, **kwargs)

                line = '%04d) %s\t%5s\t%5s\t%5s\t%5s\t%5s\t%5s\t%s\t%s\t%s\t%s\t%s' % (
                    num,
                    uid,
                    kwargs['friends']['total'],
                    kwargs['friends']['real'],
                    kwargs['friends']['fail'],
                    kwargs['followers']['total'],
                    kwargs['followers']['real'],
                    kwargs['followers']['fail'],
                    kwargs['user']['city'],
                    kwargs['user']['photo_100'],
                    kwargs['user']['first_name'],
                    kwargs['user']['last_name'],
                    kwargs['group_member']
                )

            self.save_info(line)
            print line


class Reposters(VKUserChecker):
    def get_user_list(self):
        users = []
        offset = self.offset
        while True:
            likes = self.api.get('likes.getList',
                type='post',
                owner_id='-' + GROUP_ID,
                item_id=self.post_id,
                filter='copies',
                count=1000,
                offset=offset
            )
            time.sleep(3)
            count = likes['count']
            users += likes['users']
            if (len(users) + self.offset) >= count:
                break
            else:
                offset += 1000
        return users


class GroupMembers(VKUserChecker):
    def get_user_list(self):
        users = []
        offset = self.offset
        while True:
            group = self.api.get('groups.getMembers',
                group_id=GROUP_ID,
                count=1000,
                offset=offset
            )
            time.sleep(3)
            count = group['count']
            users += group['users']
            if (len(users) + self.offset) >= count:
                break
            else:
                offset += 1000
        return users


# class FollowersChecker(Reposters):
#     def get_followers(self, uid):
#         users = []
#         while True:
#             followers = self.api.get('users.getFollowers', user_id=uid, fields='city', count=1000)
#             count = followers['count']
#             users += followers['items']
#             if len(users) >= count:
#                 break

#         ulsk_users, fail_users = [], []
#         for user in users:
#             if 'city' not in user or 'deactivated' in user:
#                 fail_users.append(user)
#             else:
#                 if int(user['city']) == CITY_ID:
#                     ulsk_users.append(user)
#         return len(ulsk_users), len(users), len(fail_users)


def main(argv):
    token = ''
    filename = './prize.txt'
    begin = 0
    post_id = 3
    count = 1000
    offset = 0
    try:
        opts, args = getopt.getopt(argv,"ht:f:b:p:c:o:",["token=","filename=","begin=","post=","count=","offset="])
    except getopt.GetoptError:
        print 'Get access_token => https://oauth.vk.com/authorize?client_id=[APP_ID]&scope=friends,wall,offline&redirect_uri=http://vk.com/blank.html&display=popup&v=5.5&response_type=token'
        print 'test.py -t <token> -f[./prize.txt] <filename> -b[0] <begin_number> -p[3] <post_id>'# '-c[1000] <count> -o[0] <offset>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'Get access_token => https://oauth.vk.com/authorize?client_id=[APP_ID]&scope=friends,wall,offline&redirect_uri=http://vk.com/blank.html&display=popup&v=5.5&response_type=token'
            print 'test.py -t <token> -f[./prize.txt] <filename> -b[0] <begin_number> -p[3] <post_id>'# '-c[1000] <count> -o[0] <offset>'
            sys.exit()
        elif opt in ("-t", "--token"):
            token = arg
        elif opt in ("-f", "--filename"):
            filename = arg
        elif opt in ("-b", "--begin"):
            begin = arg
        elif opt in ("-p", "--post"):
            post_id = arg
        elif opt in ("-c", "--count"):
            count = arg
        elif opt in ("-o", "--offset"):
            offset = arg

    print 'IN ', token, filename, begin, post_id, count, offset
    a = Reposters(token=token, filename=filename, begin=begin, post_id=post_id, count=count, offset=offset)
    a.sort_out()

if __name__ == "__main__":
    main(sys.argv[1:])