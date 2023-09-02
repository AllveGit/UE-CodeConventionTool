# Copyright Allve, Inc. All Rights Reserved.

import sys
from Process import includeline_rearrange
from Util import util_path

# Parsing system arguments
sys_sourcefolder_path = sys.argv[1]
sys_uprojectfile_path = sys.argv[2]
source_filepaths = util_path.get_allfiles_from_directorypath(sys_sourcefolder_path)

print('===== Start Apply CodeConvention =====')

processor_headerinclude_rearrange = includeline_rearrange.Processor(sys_sourcefolder_path, 
                                                                      sys_uprojectfile_path, 
                                                                      source_filepaths, 
                                                                      source_filepaths)
processor_headerinclude_rearrange.process()

print('===== Finish Apply CodeConvention =====')