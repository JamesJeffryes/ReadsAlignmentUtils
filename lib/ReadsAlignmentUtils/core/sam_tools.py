from script_utils import log as log
from script_utils import whereis
from subprocess import Popen, PIPE
import os
import re
import logging


class SamTools:
    """
    This class wraps functions from samtools.

    The functions in this class pivot around the bam format. i.e if the user has
    a sam file, it is expected that the user will first convert the file to
    a bam format before performing any other operation from this class on the file.
    """

    def __init__(self, config, logger=None):
        self.config = config
        self.logger = logger
        pass

    def _prepare_paths(self, ifile, ipath, ofile, opath, iext, oext):
        """
        setup input and output file paths and extensions
        """
        if ipath is None:
            ipath = ''
        if opath is None:
            opath = ipath
        if ofile is None:
            if ifile[-4:] == iext:
                ofile = ifile[:-4] + oext
            else:
                ofile = ifile + oext
        ifile = os.path.join(ipath, ifile)
        ofile = os.path.join(opath, ofile)

        return ifile, ofile

    def _check_prog(self):
        """
        Check if samtools is present in the env
        """
        progPath = whereis('samtools')
        if not progPath:
            raise RuntimeError(None, '{0} command not found in your PATH '
                                     'environmental variable. {1}'.format(
                                         'samtools', os.environ.get('PATH', '')))

    def _extractAlignmentStatsInfo(self, stats):
        """
        Extract stats from line format and return as dict
        """
        lines = stats.splitlines()

        # patterns
        two_nums = re.compile(r'^(\d+) \+ (\d+)')
        # two_pcts = re.compile(r'\(([0-9.na\-]+)%:([0-9.na\-]+)%\)')
        # alignment rate
        m = two_nums.match(lines[0])
        total_qcpr = int(m.group(1))
        total_qcfr = int(m.group(2))
        total_read = total_qcpr + total_qcfr

        m = two_nums.match(lines[4])
        mapped_r = int(m.group(1))
        unmapped_r = int(total_read - mapped_r)
        alignment_rate = float(mapped_r) / float(total_read) * 100.0
        if alignment_rate > 100:
            alignment_rate = 100.0

        # singletons
        m = two_nums.match(lines[10])
        singletons = int(m.group(1))
        m = two_nums.match(lines[8])
        properly_paired = int(m.group(1))
        multiple_alignments = 0

        # Create Workspace object
        stats_data = {
            # "alignment_id": sample_id,
            "alignment_rate": alignment_rate,
            "multiple_alignments": multiple_alignments,
            "properly_paired": properly_paired,
            "singletons": singletons,
            "total_reads": total_read,
            "unmapped_reads": unmapped_r,
            "mapped_reads": mapped_r
        }
        return stats_data

    def _is_valid(self, result, ignore):
        """
        Returns False if result contains errors not listed in the ignore list,
        else returns True
        :param result:
        :param ignore:
        :return:
        """
        if result is None:
            return True
        if ignore is None:
            ignore = ['xxx']  # ignore no errors

        if 'Exception' in result:
            return False

        lines = result.splitlines()
        for line in lines:
            m = re.search('(?<=ERROR:)\w+', line)
            if m is not None and m.group(0) not in ignore:
                return False

        return True

    def convert_sam_to_sorted_bam(self, ifile, ipath=None, ofile=None, opath=None,
                                  validate=False, ignore=['MATE_NOT_FOUND', 'MISSING_READ_GROUP',
                                                          'INVALID_MAPPING_QUALITY']):
        """
        Converts the specified sam file to a sorted bam file.

        throws exceptions if input file is missing, invalid or if the output file could
        not be written to disk

        :param ifile: sam file name
        :param ipath: path to sam file. If None, ipath is set to current path
        :param ofile: sorted bam file name. If None, ifile name is used with the
        extension '.sam' (if any) replaced with '.bam'
        :param opath: path to sorted bam file. If None, ipath will be used
        :param validate: set to true if sam file needs to be validated. Default=False
        :param ignore: see validate() method param

        :returns 0 if successful, else 1
        """
        # prepare input and output file paths
        ifile, ofile = self._prepare_paths(ifile, ipath, ofile, opath, '.sam', '.bam')

        # check if input file exists
        if not os.path.exists(ifile):
            raise RuntimeError(None, 'Input sam file does not exist: ' + str(ifile))

        # validate input sam file
        if validate and self.validate(ifile, ipath=None, ignore=ignore) == 1:
            return 1

        # convert
        self._check_prog()

        # samtools view -bS ifile | samtools sort -l 9 -O BAM > ofile
        try:
            sort = Popen(
                'samtools sort -l 9 -O BAM > {0}'.format(ofile),
                shell=True,
                stdin=PIPE,
                stdout=PIPE)
            view = Popen('samtools view -bS {0}'.format(ifile), shell=True, stdout=sort.stdin)
            result, stderr = sort.communicate()  # samtools always returns success
            view.wait()
        except Exception as ex:
            log('failed to convert {0} to {1}'.format(ifile, ofile) +
                '. ' + ex.message, logging.ERROR)

        return 0

    def convert_bam_to_sam(self, ifile, ipath=None, ofile=None, opath=None,
                           validate=False, ignore=['MATE_NOT_FOUND', 'MISSING_READ_GROUP',
                                                   'INVALID_MAPPING_QUALITY']):
        """
        Converts the specified bam file to a sam file.

        throws exceptions if input file is missing, invalid or if the output file could
        not be written to disk

        :param ifile: bam file name
        :param ipath: path to bam file. If None, ipath is set to current path
        :param ofile: sam file name. If None, ifile name is used with the
        extension '.bam' (if any) replaced with '.sam'
        :param opath: path to sam file. If None, ipath will be used
        :param validate: set to true if sam file needs to be validated. Default=False
        :param ignore: see validate() method param

        :returns 0 if successful, else 1
        """
        # prepare input and output file paths
        ifile, ofile = self._prepare_paths(ifile, ipath, ofile, opath, '.sam', '.bam')

        # check if input file exists
        if not os.path.exists(ifile):
            raise RuntimeError(None, 'Input bam file does not exist: ' + str(ifile))

        # validate input sam file
        if validate and self.validate(ifile, ipath=None, ignore=ignore) == 1:
            return 1

        # convert
        self._check_prog()

        # samtools view -h ifile > ofile
        try:
            convert = Popen('samtools view -h {0} > {1}'.format(ifile, ofile),
                            shell=True, stdin=PIPE, stdout=PIPE)
            convert.communicate()
        except Exception as ex:
            log('failed to convert {0} to {1}'.format(ifile, ofile) +
                '. ' + ex.message, logging.ERROR)

        return 0

    def create_bai_from_bam(self, ifile, ipath=None, ofile=None, opath=None,
                            validate=False, ignore=['MATE_NOT_FOUND', 'MISSING_READ_GROUP',
                                                    'INVALID_MAPPING_QUALITY']):
        """
        creates a bai file from a bam file

        throws exceptions if input file is missing, invalid or if the output file could
        not be written to disk

        :param ifile: bam file name
        :param ipath: path to bam file. If None, ipath is set to current path
        :param ofile: bai file name. If None, ifile name is used with the
        extension '.bam' (if any) replaced with '.bai'
        :param opath: path to bai file. If None, ipath will be used
        :param validate: set to true if sam file needs to be validated. Default=False
        :param ignore: see validate() method param

        :returns 0 if successful, else 1
        """
        # prepare input and output file paths
        ifile, ofile = self._prepare_paths(ifile, ipath, ofile, opath, '.bam',
                                           '.bai')

        # check if input file exists
        if not os.path.exists(ifile):
            raise RuntimeError(None,
                               'Input bam file does not exist: ' + str(ifile))

        # validate input sam file
        if validate and self.validate(ifile, ipath=None, ignore=ignore) == 1:
            return 1

        # convert
        self._check_prog()

        #  samtools index ifile ofile
        try:
            create = Popen('samtools index {0} {1}'.format(ifile, ofile),
                           shell=True, stdin=PIPE, stdout=PIPE)
            create.communicate()
        except Exception as ex:
            log('failed to convert {0} to {1}'.format(ifile, ofile) +
                '. ' + ex.message, logging.ERROR)

        return 0

    def get_stats(self, ifile, ipath=None):
        """
        Generate simple statistics from a BAM file. The statistics collected include
        counts of aligned and unaligned reads as well as all records with no start
        coordinate.

        :param ifile: bam file name
        :param ipath: path to bam file. If None, ipath is set to current path
        """
        if ipath is None:
            ipath = ''
        ifile = os.path.join(ipath, ifile)

        # check if input file exists
        if not os.path.exists(ifile):
            raise RuntimeError(None,
                               'Input bam file does not exist: ' + str(ifile))

        # get stats
        self._check_prog()

        try:
            # samtools flagstat ifile
            stats = Popen('samtools flagstat {0}'.format(ifile),
                          shell=True, stdin=PIPE, stdout=PIPE)
            stats, stderr = stats.communicate()

            result = self._extractAlignmentStatsInfo(stats)

        except Exception as ex:
            log('failed to get stats from {0}'.format(ifile) + '. ' + ex.message, logging.ERROR)

        return result

    def validate(self, ifile, ipath=None,
                 ignore=['MATE_NOT_FOUND', 'MISSING_READ_GROUP',
                         'INVALID_MAPPING_QUALITY']):
        """
        Validates the input bam file. Logs the errors if errors are found

        :param ifile: bam file name
        :param ipath: path to bam file. If None, ipath is set to current path
        :param ignore: list of errors to ignore (see
        http://broadinstitute.github.io/picard/command-line-overview.html#ValidateSamFile)
        :returns 0 if successful, else 1
        """
        if ipath is None:
            ipath = ''
        ifile = os.path.join(ipath, ifile)

        # check if input file exists
        if not os.path.exists(ifile):
            raise RuntimeError(None,
                               'Input bam file does not exist: ' + str(ifile))

        try:
            # java -jar picard.jar ValidateSamFile I=ifile MODE=SUMMARY
            validation = Popen(
                '/usr/lib/jvm/java-8-oracle/bin/java -jar '
                '/opt/picard/build/libs/picard.jar ValidateSamFile I={0} '
                'MODE=SUMMARY'.format(ifile),
                shell=True, stdin=PIPE, stdout=PIPE)
            result, stderr = validation.communicate()

            if self._is_valid(result, ignore):
                log('{0} passed validation'.format(ifile), logging.INFO, self.logger)
                return 0
            else:
                log('{0} failed validation with errors: {1}'.format(
                    ifile, result), logging.ERROR, self.logger)
                return 1

        except Exception as ex:
            log('{0} failed validation'.format(ifile) +
                '. ' + ex.message, logging.ERROR, self.logger)
            return 1
