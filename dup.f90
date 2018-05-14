program main

implicit none

integer :: scale

integer :: pcount, m, lc, lc1, lc2, lc3
integer :: np0, np

double precision, allocatable :: particles(:,:)
character(len=5) :: char5

write(*,"(/2x,'Reading initial particles data')")

open(file='../np_00001/particle_input.dat',unit=1000)
read(1000,*) pcount
pcount = 78208
allocate(particles(pcount,8))
do lc=1,pcount
   read(1000,*) particles(lc,1:8)
   write(*,*) particles(lc,1), particles(lc,8)
enddo
close(1000)

write(*,"(/13x,'np_00001.  Particle Count: ',I8)") pcount

do scale=2,2
   np = 0
   np0 = pcount*(scale**3)
   write(char5,"(I5.5)") scale**3

   write(*,"(2x,'Generating np_',A5,'.  Particle Count: ',I8)") char5, np0

   open(file='../np_'//char5//'/particle_input.dat',unit=1000,status='replace')
   write(1000,*) np0

   do lc3=0,scale-1
       do lc2=0,scale-1
          do lc1=0,scale-1
             do lc=1,pcount
                !write(*,"(I2,I2,I2)") lc1, lc2, lc3
               ! write(*,*) particles(lc,1)+dble(lc1)*(0.4d0/100)
                ! write(*,*) 1,particles(lc,1)+dble(lc1)*(0.4d0/100), &
               !    particles(lc,2)+dble(lc2)*(0.4d0/100), &
               !    particles(lc,3)+dble(lc3)*(0.4d0/100), &
               !    particles(lc,4), &
               !    particles(lc,5), &
               !    particles(lc,6:8)
                write(1000,100) 1,particles(lc,1)+dble(lc1)*(0.4d0/100), &
                   particles(lc,2)+dble(lc2)*(0.4d0/100), &
                   particles(lc,3)+dble(lc3)*(0.4d0/100), &
                   particles(lc,4), &
                   particles(lc,5), &
                   particles(lc,6:8)
                np = np + 1
             enddo
          enddo
       enddo
   enddo
   close(1000)

   if(np /= np0) then
      write(*,*) 'particle mismatch :: ',np0, np
      stop 3322
   endif
enddo

100     FORMAT (i1,2x,8(e2.6,2x))

end program main
