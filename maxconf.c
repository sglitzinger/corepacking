#include <stdio.h>
#include <stdlib.h>

typedef struct rect{
    double width, height;
} rect_t;

typedef struct conf{
    int numtotal;
    int numrows;
    int maxnumperrow;
    int* numperrow;
} conf_t;

typedef struct scene{
    rect_t* fpga;
    rect_t* big;
    rect_t* little;
    int maxnumbigperrow;
    int maxnumbigrows;
    int* maxnumlittleperbigconf;
} scene_t;

conf_t* createconf(int numtotal,int numrows,int maxnumperrow){
    conf_t* cf;

    cf = (conf_t*)malloc(sizeof(conf_t));
    cf->numtotal = numtotal;
    cf->numrows = numrows;
    cf->maxnumperrow = maxnumperrow;
    cf->numperrow = (int*)malloc(numrows * sizeof(int));

    return cf;
}

void destroyconf(conf_t* cf){
    free(cf->numperrow);
    free(cf);
}

void setnumatindex(conf_t* cf,int index,int val){
    cf->numperrow[index] = val;
}

int getnumatindex(conf_t* cf,int index){
    if((index >= 0) && (index < cf->numrows)) return cf->numperrow[index];
    else return 0;
}

void printconf(conf_t* cf)
{
    for (int i=cf->numrows-1; i>=0; i--) {
        printf("\n row%d: %d bigs", i, getnumatindex(cf, i) );
    }
    printf("\n");
}

void firstconf(conf_t* cf){
    int numtotal;
    int num;
    int row;

    numtotal = cf->numtotal;
    // printf("firstconf for %d cores\n",numtotal);
    row = 0;
    do{
        if(numtotal > (cf->maxnumperrow)) num = cf->maxnumperrow; else num = numtotal;
        // printf("row %d: %d cores of %d cores\n",row,num,numtotal);
        cf->numperrow[row] = num;
        numtotal -= num;
        row++;
    }while(numtotal > 0);

    for(;row<cf->numrows;row++) cf->numperrow[row] = 0;
}

// returns 1 if lastconf
int nextconf(conf_t* cf){
    int res = 0;
    int row;
    int r0,r1;

    for(row = cf->numrows -1; row >= 1;row--){
        r0 = getnumatindex(cf,row);
        r1 = getnumatindex(cf,row-1);
        if(r0 < r1 - 1){
            setnumatindex(cf,row,r0+1);
            setnumatindex(cf,row-1,r1-1);
            break;
        }
    }
    if(row == 0) res = 1;

    return res;
}

rect_t* createrect(double width,double height){
    rect_t* rptr;

    rptr = (rect_t*)malloc(sizeof(rect_t));
    rptr->width = width;
    rptr->height = height;
    return rptr;
}

double rectheight(rect_t* rptr){ return rptr->height; }

double rectwidth(rect_t* rptr){ return rptr->width; }

void printrect(char* s,rect_t* rptr){
    printf("%s: %lf x %lf\n",s,rptr->width,rptr->height);
}

void destroyrect(rect_t* rptr){ free(rptr); }

int maxnumberatwidth(double aw,double bw){
int res;

res = (int)(bw/aw);
return res;
}

scene_t* createscene(double fw,double fh,double bw,double bh,double lw,double lh){
    scene_t* sc;

    sc = (scene_t*)malloc(sizeof(scene_t));
    sc->fpga = createrect(fw,fh);
    sc->big = createrect(bw,bh);
    sc->little = createrect(lw,lh);
    sc->maxnumbigperrow = maxnumberatwidth(rectwidth(sc->big),rectwidth(sc->fpga));
    sc->maxnumbigrows = maxnumberatwidth(rectheight(sc->big),rectheight(sc->fpga));
    sc->maxnumlittleperbigconf = (int*)malloc((sc->maxnumbigperrow * sc->maxnumbigrows + 1)*sizeof(int));
    return sc;
}

void destroyscene(scene_t* sc){
    destroyrect(sc->fpga);
    destroyrect(sc->big);
    destroyrect(sc->little);
    free(sc->maxnumlittleperbigconf);
    free(sc);
}

void printscene(scene_t* sc){
    printrect("fpga  ",sc->fpga);
    printrect("big   ",sc->big);
    printrect("little",sc->little);
    printf("%d x %d bigs possible\n",sc->maxnumbigperrow,sc->maxnumbigrows);
}

int maxnumbiginscene(scene_t* sc){
    return sc->maxnumbigperrow * sc->maxnumbigrows;
}

void setmaxnumlittleperbigconf(scene_t* sc,int i,int maxnumlittle){
    sc->maxnumlittleperbigconf[i] = maxnumlittle;
}

int computemaxnumlittleperbigconf(scene_t* sc,conf_t* cf){
    int numlittle = 0;
    int maxnumlittlerows;
    int num;
    int i;
    int n;
    int rowindex;
    double h,w;
    FILE *fp;

    maxnumlittlerows = maxnumberatwidth(rectheight(sc->little),rectheight(sc->fpga));
    int littlesperrow[maxnumlittlerows];
 //   printf("%d little rows\n",naxnumlittlerows);
    for(i=1;i<=maxnumlittlerows;i++){
        h = rectheight(sc->fpga) - i*rectheight(sc->little);
        rowindex = maxnumberatwidth(rectheight(sc->big),h);
        n = getnumatindex(cf,rowindex);
        w = rectwidth(sc->fpga) - n * rectwidth(sc->big);
        num = maxnumberatwidth(rectwidth(sc->little),w);
//        printf("")
        numlittle += num;
        littlesperrow[i-1] = num;
    }

    fp = fopen("./configurations_maxconf.csv", "a");
    for(i=0;i<cf->numrows;i++)
    {
        fprintf(fp, "%d", cf->numperrow[i]);
        if(i<cf->numrows-1) fprintf(fp, ";");
        else fprintf(fp, ",");
    }
    for(i=0;i<maxnumlittlerows;i++)
    {
        fprintf(fp, "%d", littlesperrow[i]);
        if(i<maxnumlittlerows-1) fprintf(fp, ";");
        else fprintf(fp, "\n");
    }
    fclose(fp);

    return numlittle;
}

int computemaxnumlittleperbignum(scene_t* sc,int i){
    conf_t* cf;
    int maxlittlenum = 0;
    int littlenum;
    int flag;

    cf = createconf(i,sc->maxnumbigrows,sc->maxnumbigperrow);
    // printf("create conf with %d big cores\n",i);
    firstconf(cf);
    do{
        printconf(cf);
        littlenum = computemaxnumlittleperbigconf(sc,cf);
        // printf("number of littles %d\n\n",littlenum);
        if(littlenum > maxlittlenum) maxlittlenum = littlenum;
        flag = nextconf(cf);
    }while(!flag);
    destroyconf(cf);
    return maxlittlenum;
}

int main(int argc,char* argv[]){
    scene_t* sc;
    int maxnumbig;
    int i;
    int maxnumlittle;

    sc = createscene(9.55,9.55,5.00,3.80,2.10,1.81); // correct areas of 91.2, 19, and 3.8 mm^2 for fpga, big, little, respectively.
    // aspect ratios from anandtech figure and xilinx figure
    printscene(sc);

    maxnumbig = maxnumbiginscene(sc);
    for(i=0;i<=maxnumbig;i++){
        maxnumlittle = computemaxnumlittleperbignum(sc,i);
        setmaxnumlittleperbigconf(sc,i,maxnumlittle);
        printf("%d %d\n",i,maxnumlittle);
    }

    destroyscene(sc);

    return 0;
}
