# Copyright Allve, Inc. All Rights Reserved.

import re
from Util import util_path, util_regex

class Processor:
    def __init__(self, source_folderpath, uproject_filepath, source_filepaths, target_filepaths):
        self.source_folderpath = source_folderpath
        self.uproject_filepath = uproject_filepath
        self.source_filepaths = source_filepaths
        self.target_filepaths = target_filepaths

        # 순차적인 언리얼 모듈이름들
        self.uemodules = self.get_uemodulenames()

        # 파일을 write할 때 지워야 할 line들
        self.set_removelines = set()
        for uemodule in self.uemodules:
            self.set_removelines.add('//' + uemodule) # 원래파일에 있는 모듈정의 주석은 지워져야 함

        # 체크용 정규식들
        self.re_headerincludeline = re.compile(r'^#include\s.+')
        self.re_pragmaonceline = re.compile(r'^#pragma\sonce')
        self.re_startifline = re.compile(r'^#if\s.+')
        self.re_endifline = re.compile(r'^#endif')
        self.re_copyrightline = re.compile(r'^//\s?Copyright.+')

        # 헤더가 위치해있는 모듈이름을 캐싱해놓은 dict
        # Key: 헤더경로
        # Value: 위치한 모듈이름
        self.cached_dict_headermodule = dict()

        # 각 파일이 include하는 헤더경로들을 캐싱해놓은 dict
        # Key: 파일경로
        # Value: include하는 헤더경로 list
        self.cached_dict_includeheaders_perfile = dict()

    def process(self):
        print('Step: Start HeaderInclude Rearrange')
        for target_filepath in self.target_filepaths:
            if self.__parse(target_filepath) == False:
                continue
            if self.__apply(target_filepath) == False:
                continue
            print("Success HeaderInclude Rearrange to {}".format(target_filepath))

    def __parse(self, filepath) -> bool:
        is_headerfile = util_path.is_headerfile(filepath)
        is_cppfile = util_path.is_cppfile(filepath)
        if is_headerfile == False and is_cppfile == False:
            return False
        
        preprocessor_stackcnt = 0
        try:
            rf = open(filepath, 'rt', encoding='utf-8-sig')
            for line in rf.readlines():
                re_checkline = line.strip()
                # 전처리 지시문 사이는 무시
                if util_regex.is_match(self.re_startifline, re_checkline):
                    preprocessor_stackcnt += 1
                if util_regex.is_match(self.re_endifline, re_checkline):
                    preprocessor_stackcnt -= 1
                if preprocessor_stackcnt > 0:
                    continue
                # 헤더 include문이 아니면 무시
                if util_regex.is_match(self.re_headerincludeline, re_checkline) == False:
                    continue

                headerpath = line.strip()
                headerpath = headerpath.replace('#include ', '')
                headerpath = headerpath.replace('\"', '')
                headerpath = headerpath.replace('\n', '')
                if not headerpath in self.cached_dict_headermodule:
                    module = self.get_module_headerplaced(headerpath)
                    self.cached_dict_headermodule[headerpath] = module

                if not filepath in self.cached_dict_includeheaders_perfile:
                    self.cached_dict_includeheaders_perfile[filepath] = list()
                self.cached_dict_includeheaders_perfile[filepath].append(headerpath)
            rf.close()
        except Exception as e:
            print(e)
            return False
        return True

    def __apply(self, filepath) -> bool:
        is_headerfile = util_path.is_headerfile(filepath)
        is_cppfile = util_path.is_cppfile(filepath)
        if is_headerfile == False and is_cppfile == False:
            return False
        
        preprocessor_stackcnt = 0
        need_remove_whitespace = False
        is_rewrited_headers = False
        is_firstline = True
        
        rf = open(filepath, 'rt', encoding='utf-8-sig')
        origin_filelines = rf.readlines()
        rf.close()
        try:
            wf = open(filepath, 'wt', encoding='utf-8')
            for origin_fileline in origin_filelines:
                # BOM 제거
                if is_firstline == False:
                    origin_fileline = origin_fileline.replace('\ufeff', '')

                re_checkline = origin_fileline.strip()
                # 전처리 지시문 사이는 무시
                if util_regex.is_match(self.re_startifline, re_checkline):
                    preprocessor_stackcnt += 1
                if util_regex.is_match(self.re_endifline, re_checkline):
                    preprocessor_stackcnt -= 1
                if preprocessor_stackcnt > 0:
                    wf.write(origin_fileline)
                    continue
                # 헤더 include문이면 무시
                if util_regex.is_match(self.re_headerincludeline, re_checkline):
                    continue
                # 무시해야 할 line이면 무시
                if re_checkline in self.set_removelines:
                    continue

                # 이전에 생성했던 공백제거
                if need_remove_whitespace:
                    if re_checkline == '' or re_checkline == '\n':
                        continue
                    need_remove_whitespace = False

                # 헤더파일이면, pragma once문 뒤에 헤더참조라인들을 삽입해준다.
                if is_rewrited_headers == False:
                    if is_headerfile: 
                        if util_regex.is_match(self.re_pragmaonceline, re_checkline):
                            wf.write(origin_fileline)
                            wf.write('\n')
                            self.write_includeheaderlines(filepath, wf)
                            need_remove_whitespace = True
                            is_rewrited_headers = True
                    # 소스파일이면, Copyright문 뒤, 혹은 첫번째라인에 헤더참조라인들을 삽입해준다.
                    elif is_cppfile and is_firstline:
                        if util_regex.is_match(self.re_copyrightline, re_checkline):
                            wf.write(origin_fileline)
                            wf.write('\n')
                            self.write_includeheaderlines(filepath, wf)
                        else:
                            self.write_includeheaderlines(filepath, wf)
                            wf.write('\n')
                            wf.write(origin_fileline)
                        need_remove_whitespace = True
                        is_rewrited_headers = True
                else:
                    wf.write(origin_fileline)
                is_firstline = False
            wf.close()
        except Exception as e:
            print(e)
            wf = open(filepath, 'wt', encoding='utf-8')
            wf.writelines(origin_filelines)
            wf.close()
            return False
        return True

    def get_uemodulenames(self) -> list[str]:
        is_modulepart = False
        moduledepth = 0
        modulenames = ['Matched', 'UE']
        f = open(self.uproject_filepath, 'r', encoding='utf-8-sig')
        for fileline in f.readlines():
            if "Modules" in fileline:
                is_modulepart = True
            if is_modulepart:
                if '[' in fileline:
                    moduledepth += 1
                if ']' in fileline:
                    moduledepth -= 1
                if moduledepth <= 0:
                    break
                if "\"Name\"" in fileline:
                    modulename = fileline
                    modulename = modulename.replace('\t\t\t', '')
                    modulename = modulename.replace('\"', '')
                    modulename = modulename.replace('Name', '')
                    modulename = modulename.replace(':', '')
                    modulename = modulename.replace(',', '')
                    modulename = modulename.strip()
                    modulenames.append(modulename)
        f.close()
        modulenames.append('Gen')
        return modulenames
    
    def get_module_headerplaced(self, headerpath) -> str:
        if 'generated.h' in headerpath:
            return 'Gen'
        search_headerpath = '/' + headerpath
        for source_filepath in self.source_filepaths:
            if not search_headerpath in source_filepath:
                continue
            res = source_filepath.split('/Source/')
            res = res[1].split('/')
            return res[0]
        return 'UE'
    
    def write_includeheaderlines(self, filepath, wf):
        if not filepath in self.cached_dict_includeheaders_perfile:
            return

        matched_headerpath = ''
        if util_path.is_cppfile(filepath):
            fileext = util_path.get_file_extension(filepath)
            matched_headerpath = filepath.removesuffix(fileext) + '.h'

        dict_includeheader_permodule = dict()
        for headerpath in self.cached_dict_includeheaders_perfile[filepath]:
            if ('/' + headerpath) in matched_headerpath:
                module = 'Matched'
            else:
                module = self.cached_dict_headermodule[headerpath]
            if not module in dict_includeheader_permodule:
                dict_includeheader_permodule[module] = list()
            dict_includeheader_permodule[module].append(headerpath)
        
        for uemodule in self.uemodules:
            if not uemodule in dict_includeheader_permodule:
                continue
            wf.write('//' + uemodule)
            wf.write('\n')
            dict_includeheader_permodule[uemodule].sort()
            for headerpath in dict_includeheader_permodule[uemodule]:
                if '<' in headerpath:
                    wf.write("#include {}".format(headerpath))
                else:
                    wf.write("#include \"{}\"".format(headerpath))
                wf.write('\n')
            wf.write('\n')
