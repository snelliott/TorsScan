import os
import logging
from qtc import patools as pa
from qtc import iotools as io
from qtc import obtools as ob
log = logging.getLogger(__name__)

class RESULTS:
    def __init__(self, args, paths):
        self.args = args
        self.set_levels()

        import sys
 
    def set_levels(self):
        optlevel = ''
        taulevel = ''
        if '1' in self.args.xyzstart:
            if len(self.args.XYZ.split('/')) >  2:
                optlevel = self.args.XYZ
        else:
            for meth in self.args.meths:
                if meth[0] == 'level1':
                    optlevel = '{}/{}'.format(meth[1],meth[2])
                elif meth[0] == 'level0':
                    optlevel = '{}/{}'.format(meth[1],meth[2])
                elif 'tau' in meth[0]:
                    taulevel = '{}/{}'.format(meth[1], meth[2])
        
        anlevel  = ''
        if self.args.anharm.lower() != 'false':
            split = self.args.anharm.split('/')
            if len(split) > 3:
                anlevel =  '{}/{}/{}'.format(split[3],split[4],split[5])
            elif len(split) == 3:
                anlevel =  '{}/{}/{}'.format(split[0],split[1],split[2])
            else:
                for meth in self.args.meths:
                    if str(self.args.anharm) in meth[0]:
                        anlevel = meth[1] + '/' +  meth[2]
        self.optlevel = optlevel.replace('g09','gaussian')
        self.taulevel = taulevel.replace('g09','gaussian')
        self.anlevel  =  anlevel.replace('g09','gaussian')
        self.enlevel  = 'optlevel'
        return

    def get_hlen(self):

        hlen     = []
        msg = ''
        for i in range(len(self.args.reacs)):
            if io.check_file('me_files/reac'+str(i+1) + '_en.me'):
                hlen.append(float(io.read_file('me_files/reac'+str(i+1) + '_en.me')))
                for meth in self.args.meths:
                    if 'hlevel' in meth:
                        self.enlevel = '{}/{}'.format(meth[1],meth[2])
            else:
               msg += 'No energy found for reac{:g}\n'.format(i+1)

        for i in range(len(self.args.prods)):
            if io.check_file('me_files/prod'+str(i+1) + '_en.me'):
                hlen.append(float(io.read_file('me_files/prod'+str(i+1) + '_en.me')))
            else:
               msg += 'No energy found for prod{:g}\n'.format(i+1)

        if self.args.reactype:
            if io.check_file('me_files/ts_en.me'):
                hlen.append(float(io.read_file('me_files/ts_en.me')))
            else:
                msg += 'No energy found for ts\n'
            if self.args.wellr and self.args.wellr.lower() != 'false':
                if io.check_file('me_files/wellr_en.me'):
                    hlen.append(float(io.read_file('me_files/wellr_en.me')))
                else:
                   msg += 'No energy found for wellr\n'
            if self.args.wellp and self.args.wellp.lower() != 'false':
                if io.check_file('me_files/wellp_en.me'):
                    hlen.append(float(io.read_file('me_files/wellp_en.me')))
                else:
                   msg += 'No energy found for wellp\n'
        log.warning(msg)
        self.hlen = hlen
        return hlen
 
    def parse(self, n, species, lines, lines2=''):
        """
        Parses, prints, and stores the quantum chemistry and thermochemistry output
        """
        printstr = '\n=====================\n          '+species+'\n=====================\n'
        d = {}
        prog   = ''
        method = '' 
        basis  = ''
        energy = ''
        optprog, optmethod, optbasis = self.optlevel.split('/')
        if self.enlevel == 'optlevel':
            prog   =  pa.get_prog(lines) 
            method =  pa.method(lines)
            if method:
                method  = method.lower().lstrip('r')
            basis  =  pa.basisset(lines).lower() 
            energy = pa.energy(lines)[1]
        elif len(self.enlevel.split('/')) > 2 :
            prog, method, basis = self.enlevel.split('/') 
            if len(self.hlen) >= n:
                energy = self.hlen[n-1]
            else:
                energy = 'N/A'
        zmat=  pa.zmat(lines)   
        geo =  pa.geo(lines)
        xyz =  pa.xyz(lines)
        rotcon = pa.rotconsts(lines)
        d[  'prog'] = prog
        d['method'] = method
        d[ 'basis'] = basis
        d['energy'] = energy
        d[  'zmat'] = zmat
        d[   'geo'] = geo
        d[   'xyz'] = xyz
        d['rotconsts'] = rotcon
        if rotcon:
            rotcon = ', '.join(rotcon)
        freqs  =  pa.freqs(lines)
        if freqs:
            d[ 'freqs'] = freqs
            freqs   = ', '.join(freq for freq in freqs[::-1])
    
        if lines2 != '':
            try:
                pfreqs  = pa.EStokTP_freqs(lines2)
            except:
                pfreqs  = []
            d['pfreqs'] = pfreqs
            pfreqs  = ', '.join('{:>9}'.format(freq) for freq in pfreqs)
        else: 
            pfreqs = []

    
        printstr += 'Optimized at : {}\n'.format(self.optlevel)
        printstr += 'Energy: ' + str(energy) + ' A.U.\n'
        printstr += 'Prog  : ' + str(prog  ) + '\n'
        printstr += 'Method: ' + str(method) + '\n' 
        printstr += 'Basis:  ' + str(basis ) + '\n'
        printstr += 'Rotational Constants: ' + str(rotcon)  + ' GHz\n'
        printstr += 'Zmatrix (Angstrom):\n' + str(   zmat)   + '\n'
        if xyz != None:
            printstr += 'Cartesian coordinates (Angstrom):\n' + str(xyz)
        printstr += '\nUnprojected Frequencies (cm-1):\t'  + str(freqs)
        if lines2:
            printstr += '\nProjected Frequencies   (cm-1):\t'  + pfreqs

        if self.args.store:
            database = self.args.database 
            io.db_store_opt_prop(zmat,  species,'zmat', database, optprog, optmethod, optbasis)
            io.db_store_opt_prop(freqs, species, 'hrm', database, optprog, optmethod, optbasis)
            io.db_store_sp_prop(energy, species, 'ene', database,    prog,    method,    basis, optprog, optmethod, optbasis)
            io.db_store_sp_prop(rotcon, species,  'rc', database,    prog,    method,    basis, optprog, optmethod, optbasis)
            if xyz != None:
                io.db_store_opt_prop(geo,   species, 'geo', database, optprog, optmethod, optbasis)
                io.db_store_opt_prop(xyz,   species, 'xyz', database, optprog, optmethod, optbasis)
            if lines2:                                              
                io.db_store_opt_prop(pfreqs, species,'phrm', database, optprog, optmethod, optbasis)
        return printstr, d 

    def parse_thermo(self, n, species, d):
        printstr = '\n=====================\n          '+species+'\n=====================\n'
        optprog, optmethod, optbasis = self.optlevel.split('/')
        if self.enlevel == 'optlevel':
            prog   =  optprog
            method =  optmethod
            basis  =  optbasis
        else:
            prog, method, basis = self.enlevel.split('/') 
        d[  'prog'] = prog
        d['method'] = method
        d[ 'basis'] = basis
        if self.args.anharm != 'false':
            anpfr     = ', '.join('%4.4f' % freq for freq in self.anfreqs[n-1])
            pxmat     =('\n\t'.join(['\t'.join(['%3.3f'%item for item in row]) 
                        for row in self.anxmat[n-1]]))
            printstr += '\nAnharmonic Frequencies  (cm-1):\t' + anpfr
            printstr += '\nX matrix:\n\t' + pxmat #+   anxmat[i-1]
            d['panharm'] = anpfr
            d[  'pxmat'] = pxmat
        printstr += '\nHeat of formation(  0K): {0:.2f} kcal / {1:.2f}  kJ\n'.format(self.dH0[n-1],   self.dH0[n-1]/.00038088/ 627.503)
        printstr +=   'Heat of formation(298K): {0:.2f} kcal / {1:.2f}  kJ\n'.format(float(self.dH298[n-1]), float(self.dH298[n-1])/.00038088/ 627.503)
        d[   'dH0K'] = self.dH0
        d[ 'dH298K'] = self.dH298
        if self.args.store:
            database = self.args.database 
            if self.args.anharm != 'false':
                anprog, anmethod, anbasis = anlevel.split('/')
                io.db_store_sp_prop(anpfr, species, 'panhrm', database,  anprog, anmethod, anbasis, optprog, optmethod, optbasis)
                io.db_store_sp_prop(pxmat, species,  'pxmat', database,  anprog, anmethod, anbasis, optprog, optmethod, optbasis) 
            if not io.check_file(io.db_sp_path(prog, method, basis, database, species, optprog, optmethod, optbasis) + '/' + species + '.hf298k'):
                io.db_store_sp_prop('Energy (kcal)\tBasis\n----------------------------------\n',species,'hf298k',database, prog,method,basis, optprog, optmethod, optbasis)
            if len(self.hfbases) >= n+1:
                io.db_append_sp_prop(str(self.dH298[n-1]) + '\t' + ', '.join(self.hfbases[n]) + '\n', species, 'hf298k',database, prog,method,basis, optprog, optmethod, optbasis)
        return printstr, d
 
#    def ts_parse(self, lines):
#        """
#        Similar to parse, but only for TS
#        """
#        tstype = ['TS', 'WELLR', 'WELLP']
#        printstr= '=====================\n          '+tstype[n]+'\n=====================\n'
#        prog   =  pa.get_prog(lines) 
#        method =  pa.method(  lines).lower().lstrip('r')
#        basis  =  pa.basisset(lines).lower() 
#        energy = str(pa.energy(lines)[1]) 
#        zmat   =  pa.zmat(    lines)    
#        xyz    =  pa.xyz(     lines) 
#        rotcon = ', '.join(pa.rotconsts(lines))
#        freqs  = ', '.join(freq for freq in pa.freqs(lines)[::-1])
#        return printstr

    def get_results(self):

       msg = printheader()
       d = {}
       for i,reac in enumerate(self.args.reacs, start=1):
           lines  = ''
           if io.check_file('geoms/reac' + str(i) + '_l1.log'):
               lines   = io.read_file('geoms/reac' + str(i) + '_l1.log')
           lines2  = ''
           if io.check_file('me_files/reac' +  str(i) + '_fr.me'):
               lines2  = io.read_file('me_files/reac' +  str(i) + '_fr.me')
           if lines:
               printstr, d[reac] = self.parse(i, reac, lines, lines2)
               msg += printstr
           else:
               log.warning('No geom for ' + reac + ' in geoms/reac' + str(i) + '_l1.log')
       for j,prod in enumerate(self.args.prods, start=1):
           lines  = ''
           if io.check_file('geoms/prod' + str(i) + '_l1.log'):
               lines = io.read_file('geoms/prod' + str(j) + '_l1.log')
           lines2 = ''
           if io.check_file('me_files/reac' +  str(j) + '_fr.me'):
               lines2  = io.read_file('me_files/prod' +  str(j) + '_fr.me')
           if lines:
               printstr, d[prod] = self.parse(i+j-1, prod, lines, lines2)
               msg += printstr
           else:
               log.warning('No geom for ' + prod + '  in geoms/prod' + str(j) + '_l1.log')

       #if args.nTS > 0:
       #    lines = io.read_file('geoms/tsgta_l1.log')
       #    printstr += ts_parse(0,lines)
       #    if args.nTS > 1:
       #        lines = io.read_file('geoms/wellr_l1.log')
       #        printstr += ts_parse(1,lines)
       #        if args.nTS > 2:
       #            lines = io.read_file('geoms/wellp_l1.log')
       #            printstr += ts_parse(2,lines)
       log.info(msg)
       self.d = d
       return 

    def get_thermo_results(self):

       msg = print_thermoheader()
       d = self.d
       for i,reac in enumerate(self.args.reacs, start=1):
           if reac in d:
               printstr, d[reac] = self.parse_thermo(i, reac, d[reac])
               msg += printstr
       for j,prod in enumerate(self.args.prods, start=1):
           if prod in d:
               if self.args.reactype:
                   printstr, d[prod] = self.parse_thermo(i+j, prod, d[prod])
                   msg += printstr
               else:
                   printstr, d[prod] = self.parse_thermo(i+j-1, prod, d[prod])
                   msg += printstr
       log.info(msg)
       self.d = d
       return

def printheader():
    printstr  = '\n\n ______________________'
    printstr += '\n||                    ||'
    printstr += '\n||       OUTPUT       ||'
    printstr += '\n||____________________||\n\n'
    return printstr

def print_thermoheader():
    printstr  = '\n\n ______________________'
    printstr += '\n||                    ||'
    printstr += '\n||       THERMO       ||'
    printstr += '\n||____________________||\n\n'
    return printstr
