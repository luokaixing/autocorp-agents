# uniswap-v3


## 第 1 页

Uniswap v3 Core
March2021
HaydenAdams NoahZinsmeister MoodySalem
hayden@uniswap.org noah@uniswap.org moody@uniswap.org
RiverKeefer DanRobinson
river@uniswap.org dan@paradigm.xyz
ABSTRACT Inthispaper,wepresentUniswapv3,anovelAMMthatgives
Uniswap v3 is a noncustodial automated market maker imple- liquidityprovidersmorecontroloverthepricerangesinwhich
mentedfortheEthereumVirtualMachine.Incomparisontoearlier theircapitalisused,withlimitedeffectonliquidityfragmentation
versionsoftheprotocol,Uniswapv3providesincreasedcapital andgasinefficiency.Thisdesigndoesnotdependonanyshared
efficiencyandfine-tunedcontroltoliquidityproviders,improves assumptionaboutthepricebehaviorofthetokens.Uniswapv3
theaccuracyandconvenienceofthepriceoracle,andhasamore isbasedonthesameconstantproductreservescurveasearlier
flexiblefeestructure. versions[1],butoffersseveralsignificantnewfeatures:
• ConcentratedLiquidity:Liquidityproviders(LPs)aregiven
1 INTRODUCTION
theabilitytoconcentratetheirliquidityby“bounding"it
Automatedmarketmakers(AMMs)areagentsthatpoolliquidity withinanarbitrarypricerange.Thisimprovesthepool’s
andmakeitavailabletotradersaccordingtoanalgorithm[5].Con- capitalefficiencyandallowsLPstoapproximatetheirpre-
stantfunctionmarketmakers(CFMMs),abroadclassofAMMsof ferredreservescurve,whilestillbeingefficientlyaggregated
whichUniswapisamember,haveseenwidespreaduseinthecon- withtherestofthepool.Wedescribethisfeatureinsection
textofdecentralizedfinance,wheretheyaretypicallyimplemented 2anditsimplementationinSection6.
assmartcontractsthattradetokensonapermissionlessblockchain • Flexible Fees: The swap fee is no longer locked at 0.30%.
[2]. Rather, the fee tier for each pool (of which there can be
CFMMsastheyareimplementedtodayareoftencapitalinef- multipleperassetpair)issetoninitialization(Section3.1).
ficient. In the constant product market maker formula used by Theinitiallysupportedfeetiersare0.05%,0.30%,and1%.
Uniswapv1andv2,onlyafractionoftheassetsinthepoolare UNIgovernanceisabletoaddadditionalvaluestothisset.
available at a given price. This is inefficient, particularly when • ProtocolFeeGovernance:UNIgovernancehasmoreflexibility
assetsareexpectedtotradeclosetoaparticularpriceatalltimes. insettingthefractionofswapfeescollectedbytheprotocol
Priorattemptstoaddressthiscapitalefficiencyissue,suchas (Section6.2.2).
Curve[3]andYieldSpace[4],haveinvolvedbuildingpoolsthatuse • ImprovedPriceOracle:Uniswapv3providesawayforusers
differentfunctionstodescribetherelationbetweenreserves.This toqueryrecentpriceaccumulatorvalues,thusavoidingthe
requiresallliquidityprovidersinagivenpooltoadheretoasingle needtocheckpointtheaccumulatorvalueattheexactbe-
formula, and could result in liquidity fragmentation if liquidity ginningandendoftheperiodforwhichaTWAPisbeing
providerswanttoprovideliquiditywithindifferentpriceranges. measured.(Section5.1).
1


## 第 2 页

HaydenAdams,NoahZinsmeister,MoodySalem,RiverKeefer,andDanRobinson
• LiquidityOracle:Thecontractsexposeatime-weightedav-
erageliquidityoracle(Section5.3).
The Uniswap v2 core contracts are non-upgradeable by de-
sign, so Uniswap v3 is implemented as an entirely new set of
contracts,availablehere.TheUniswapv3corecontractsarealso
non-upgradeable,withsomeparameterscontrolledbygovernance
asdescribedinSection4.
2 CONCENTRATEDLIQUIDITY
Thedefiningideaof Uniswapv3isthatofconcentratedliquidity:
liquidityboundedwithinsomepricerange.
Inearlierversions,liquiditywasdistributeduniformlyalongthe
𝑥·𝑦=𝑘 (2.1)
reservescurve,where𝑥 and𝑦aretherespectivereservesoftwo
assetsXandY,and𝑘isaconstant[1].Inotherwords,earlierver-
sionsweredesignedtoprovideliquidityacrosstheentireprice
range(0,∞).Thisissimpletoimplementandallowsliquidityto
beefficientlyaggregated,butmeansthatmuchoftheassetsheldin
apoolarenevertouched.
Having considered this, it seems reasonable to allow LPs to
concentratetheirliquiditytosmallerpricerangesthan(0,∞).We
callliquidityconcentratedtoafiniterangeaposition.Aposition
onlyneedstomaintainenoughreservestosupporttradingwithin
itsrange,andthereforecanactlikeaconstantproductpoolwith
largerreserves(wecallthesethevirtualreserves)withinthatrange.
𝑥
real
𝑏
𝑐
𝑦
real
𝑎
XReserves
sevreseRY
liquidityiscomposedentirelyofasingleasset,becausethereserves
oftheotherassetmusthavebeenentirelydepleted.Ifthepriceever
reenterstherange,theliquiditybecomesactiveagain.
Theamountofliquidityprovidedcanbemeasuredbythevalue √
𝐿,whichisequalto 𝑘.Therealreservesofapositionaredescribed
bythecurve:
𝐿 √
(𝑥+ √ )(𝑦+𝐿 𝑝 𝑎)=𝐿2 (2.2)
𝑝
𝑏
Thiscurveisatranslationofformula2.1suchthatthepositionis
solventexactlywithinitsrange(Fig.2).
𝑏
𝑎
virtualreserves
XReserves
Figure1:SimulationofVirtualLiquidity
Specifically,apositiononlyneedstoholdenoughofassetXto
coverpricemovementtoitsupperbound,becauseupwardsprice
movement1correspondstodepletionoftheXreserves.Similarly,
itonlyneedstoholdenoughofassetYtocoverpricemovement
toitslowerbound.Fig.1depictsthisrelationshipforapositionon
arange [𝑝 𝑎 ,𝑝 𝑏] andacurrentprice𝑝 𝑐 ∈ [𝑝 𝑎 ,𝑝 𝑏].𝑥 real and𝑦 real
denotetheposition’srealreserves.
Whenthepriceexitsaposition’srange,theposition’sliquidity
is no longer active, and no longer earns fees. At that point, its
1WetakeassetYtobetheunitofaccount,whichcorrespondstotoken1inour
implementation.
sevreseRY
virtualreserves(2.1)
realreserves(2.2)
Figure2:RealReserves
Liquidityprovidersarefreetocreateasmanypositionsasthey
seefit,eachonitsownpricerange.Inthisway,LPscanapproximate
anydesireddistributionofliquidityonthepricespace(seeFig.3
forafewexamples).Moreover,thisservesasamechanismtolet
themarketdecidewhereliquidityshouldbeallocated.RationalLPs
canreducetheircapitalcostsbyconcentratingtheirliquidityin
anarrowbandaroundthecurrentprice,andaddingorremoving
tokensasthepricemovestokeeptheirliquidityactive.
2.1 RangeOrders
Positionsonverysmallrangesactsimilarlytolimitorders—ifthe
rangeiscrossed,thepositionflipsfrombeingcomposedentirely
ofoneasset,tobeingcomposedentirelyoftheotherasset(plus
accruedfees).Therearetwodifferencesbetweenthisrangeorder
andatraditionallimitorder:
• Thereisalimittohownarrowaposition’srangecanbe.
Whilethepriceiswithinthatrange,thelimitordermight
bepartiallyexecuted.
• Whenthepositionhasbeencrossed,itneedstobewith-
drawn.Ifitisnot,andthepricecrossesbackacrossthat
range,thepositionwillbetradedback,effectivelyreversing
thetrade.
2


## 第 3 页

Uniswapv3Core
0 ∞
Price
ytidiuqiL
𝑝 𝑝 𝑎 𝑏
Price
(I)Uniswapv2
ytidiuqiL
Price
(II)Asinglepositionon[𝑝𝑎,𝑝 𝑏]
ytidiuqiL
(III)Acollectionofcustompositions
Figure3:ExampleLiquidityDistributions
3 ARCHITECTURALCHANGES poolasindividualtokens,ratherthanautomaticallyreinvestedas
Uniswapv3makesanumberofarchitecturalchanges,someof liquidityinthepool.
whicharenecessitatedbytheinclusionofconcentratedliquidity, As a result, in v3, the pool contract does not implement the
andsomeofwhichareindependentimprovements. ERC-20standard.AnyonecancreateanERC-20tokencontractin
theperipherythatmakesaliquiditypositionmorefungible,but
3.1 MultiplePoolsPerPair itwillhavetohaveadditionallogictohandledistributionof,or
reinvestmentof,collectedfees.Alternatively,anyonecouldcreate
InUniswapv1andv2,everypairoftokenscorrespondstoasingle
aperipherycontractthatwrapsanindividualliquidityposition
liquiditypool,whichappliesauniformfeeof0.30%toallswaps.
(includingcollectedfees)inanERC-721non-fungibletoken.
Whilethisdefaultfeetierhistoricallyworkedwellenoughformany
tokens,itislikelytoohighforsomepools(suchaspoolsbetween 4 GOVERNANCE
twostablecoins),andtoolowforothers(suchaspoolsthatinclude
The factory has an owner, which is initially controlled by UNI
highlyvolatileorrarelytradedtokens).
tokenholders.2 The owner does not have the ability to halt the
Uniswapv3introducesmultiplepoolsforeachpairoftokens,
operationofanyofthecorecontracts.
eachwithadifferentswapfee.Allpoolsarecreatedbythesame
AsinUniswapv2,Uniswapv3hasaprotocolfeethatcanbe
factorycontract.Thefactorycontractinitiallyallowspoolstobe
createdatthreefeetiers:0.05%,0.30%,and1%.Additionalfeetiers turnedonbyUNIgovernance.InUniswapv3,UNIgovernancehas
moreflexibilityinchoosingthefractionofswapfeesthatgotothe
canbeenabledbyUNIgovernance.
protocol,andisabletochooseanyfraction 𝑁 1 where4≤𝑁 ≤10,
or0.Thisparametercanbesetonaper-poolbasis.
3.2 Non-FungibleLiquidity
UNIgovernancealsohastheabilitytoaddadditionalfeetiers.
3.2.1 Non-CompoundingFees. Feesearnedinearlierversionswere Whenitaddsanewfeetier,itcanalsodefinethetickSpacing
continuouslydepositedinthepoolasliquidity.Thismeantthat
(seeSection6.1)correspondingtothatfeetier.Onceafeetieris
liquidityinthepoolwouldgrowovertime,evenwithoutexplicit addedtothefactory,itcannotberemoved(andthetickSpacing
deposits,andthatfeeearningscompounded.
cannotbechanged).Theinitialfeetiersandtickspacingssupported
InUniswapv3,duetothenon-fungiblenatureofpositions,this are0.05%(withatickspacingof10,approximately0.10%between
isnolongerpossible.Instead,feeearningsarestoredseparately initializableticks),0.30%(withatickspacingof60,approximately
andheldasthetokensinwhichthefeesarepaid(seeSection6.2.2). 0.60%betweeninitializableticks),and1%(withatickspacingof
200,approximately2.02%betweenticks.
3.2.2 RemovalofNativeLiquidityTokens. InUniswapv1andv2,
Finally,UNIgovernancehasthepowertotransferownershipto
thepoolcontractisalsoanERC-20tokencontract,whosetokens
anotheraddress.
representliquidityheldinthepool.Whilethisisconvenient,it
actuallysitsuneasilywiththeUniswapv2philosophythatany-
5 ORACLEUPGRADES
thingthatdoesnotneedtobeinthecorecontractsshouldbeinthe
periphery,andblessingone“canonical"ERC-20implementation Uniswapv3includesthreesignificantchangestothetime-weighted
discouragesthecreationofimprovedERC-20tokenwrappers.Ar- averageprice(TWAP)oraclethatwasintroducedbyUniswapv2.
guably,theERC-20tokenimplementationshouldhavebeeninthe Mostsignificantly,Uniswapv3removestheneedforusersof
periphery,asawrapperonasingleliquiditypositioninthecore theoracletotrackpreviousvaluesoftheaccumulatorexternally.
contract. Uniswapv2requiresuserstocheckpointtheaccumulatorvalue
ThechangesmadeinUniswapv3forcethisissuebymaking atboththebeginningandendofthetimeperiodforwhichthey
completelyfungibleliquiditytokensimpossible.Duetothecustom 2Specifically,theownerwillbeinitializedtotheTimelockcontractfromUNIgover-
liquidityprovisionfeature,feesarenowcollectedandheldbythe nance,0x1a9c8182c09f50c8318d769245bea52c32be35bc.
3


### 第 3 页 表格 1

| --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |

## 第 4 页

HaydenAdams,NoahZinsmeister,MoodySalem,RiverKeefer,andDanRobinson
wantedtocomputeaTWAP.Uniswapv3bringstheaccumulator oftoken0isnotequivalenttothereciprocalofthetime-weighted
checkpointsintocore,allowingexternalcontractstocomputeon- arithmeticmeanpriceoftoken1.
chainTWAPsoverrecentperiodswithoutstoringcheckpointsof Usingthetime-weightedgeometricmeanprice,asUniswapv3
theaccumulatorvalue. does, avoids the need to track separate accumulators for these
Anotherchangeisthatinsteadofaccumulatingthesumofprices, ratios.Thegeometricmeanofasetofratiosisthereciprocalofthe
allowinguserstocomputethearithmeticmeanTWAP,Uniswap geometricmeanoftheirreciprocals.Itisalsoeasytoimplement
v3 tracks the sum of log prices, allowing users to compute the inUniswapv3becauseofitsimplementationofcustomliquidity
geometricmeanTWAP. provision,asdescribedinsection6.Inaddition,theaccumulatorcan
Finally,Uniswapv3addsaliquidityaccumulatorthatistracked bestoredinasmallernumberofbits,sinceittrackslog𝑃ratherthan
alongsidethepriceaccumulator,whichaccumulates 𝐿 1 foreach 𝑃,andlog𝑃 canrepresentawiderangeofpriceswithconsistent
second.Thisliquidityaccumulatorisusefulforexternalcontracts precision.4Finally,thereisatheoreticalargumentthatthetime-
thatwanttoimplementliquidityminingontopofUniswapv3.It weightedgeometricmeanpriceshouldbeatruerrepresentationof
canalsobeusedbyothercontractstoinformadecisiononwhich theaverageprice.5
ofthepoolscorrespondingtoapair(seesection3.1)willhavethe Insteadoftrackingthecumulativesumoftheprice𝑃,Uniswap
mostreliableTWAP. v3accumulatesthecumulativesumofthecurrenttickindex(𝑙𝑜𝑔 1.0001 𝑃,
thelogarithmofpriceforbase1.0001,whichispreciseupto1basis
5.1 OracleObservations point).Theaccumulatoratanygiventimeisequaltothesumof
AsinUniswapv2,Uniswapv3tracksarunningaccumulatorof
𝑙𝑜𝑔
1.0001
(𝑃)foreverysecondinthehistoryofthecontract:
thepriceatthebeginningofeachblock,multipliedbythenumber
𝑡
ofs
A
ec
p
o
o
n
o
d
l
s
in
si
U
nc
n
e
is
t
w
he
a
l
p
as
v
t
2
b
s
l
t
o
o
c
r
k
e
.
sonlythemostrecentvalueofthis
𝑎 𝑡 = (cid:213) log 1.0001 (𝑃 𝑖) (5.1)
𝑖=1
priceaccumulator—thatis,thevalueasofthelastblockinwhicha
Wewanttoestimatethegeometricmeantime-weightedaverage
s
is
w
t
a
h
p
e
o
r
c
e
c
s
u
p
r
o
r
n
e
s
d
i
.
b
W
ilit
h
y
en
of
c
t
o
h
m
e
p
e
u
x
t
t
i
e
n
r
g
na
a
l
ve
c
r
a
a
ll
g
e
e
r
p
to
ric
p
e
r
s
ov
in
id
U
e
n
th
is
e
w
p
a
r
p
ev
v
i
2
o
,
u
i
s
t price(𝑝 𝑡
1
,𝑡
2
)overanyperiod𝑡 1to𝑡 2.
valueofthepriceaccumulator.Withmanyusers,eachwillhaveto 1
providetheirownmethodologyforcheckpointingpreviousvalues (cid:214)
𝑡
2
𝑡2−𝑡1
oftheaccumulator,orcoordinateonasharedmethodtoreduce 𝑃 𝑡 1 ,𝑡 2 =(cid:169) (cid:173) 𝑃 𝑖(cid:170) (cid:174) (5.2)
costs.Andthereisnowaytoguaranteethateveryblockinwhich (cid:171)
𝑖=𝑡
1 (cid:172)
thepoolistouchedwillbereflectedintheaccumulator.
Tocomputethis,youcanlookattheaccumulator’svalueat𝑡
1
InUniswapv3,thepoolstoresalistofpreviousvaluesforthe andat𝑡 2,subtractthefirstvaluefromthesecond,dividebythe
priceaccumulator(aswellastheliquidityaccumulatordescribed numberofsecondselapsed,andcompute1.0001 𝑥 tocomputethe
in section 5.3). It does this by automatically checkpointing the timeweightedgeometricmeanprice.
accumulatorvalueeverytimethepoolistouchedforthefirsttime
i e n ve a n b t l u o a c l k ly ,c o y v c e li r n w g r t i h tt r e o n ug b h y a a n n a e r w ray on w e h , e s r im et i h la e r o t l o de a s c t i c r h cu ec la k r po b i u n ff t e i r s . log 1.0001 (cid:0)𝑃 𝑡 1 ,𝑡 2 (cid:1) = (cid:205) 𝑖 𝑡 = 2 𝑡 1 l 𝑡 og − 1.0 𝑡 001 (𝑃 𝑖) (5.3)
2 1
W an h y i o l n e e th ca is n a i r n r i a ti y al i i n ze iti a a d l d ly iti o o n n l a y l h st a o s ra ro ge om slo f t o s r to a l s e i n n g g t l h e e c n he th c e kp a o rr i a n y t, , log 1.0001 (cid:0)𝑃 𝑡 1 ,𝑡 2 (cid:1) = 𝑎 𝑡 𝑡 2 − −𝑡 𝑎 𝑡 1 (5.4)
extendingtoasmanyas65,536checkpoints.3 Thisimposesthe 2 1
o ar n r e a - y ti o m n e w g h a o s e c v o e s r t w of an in ts it t i h al i i s z p in a g ir a t d o d c i h ti e o c n k a p l o s i t n o t r m ag o e re sl s o l t o s ts f . orthis 𝑃 𝑡 1 ,𝑡 2 =1.0001 𝑎𝑡 𝑡 2 2 − −𝑡 𝑎 1 𝑡1 (5.5)
Thepoolexposesthearrayofpastobservationstousers,aswell
5.3 LiquidityOracle
asaconveniencefunctionforfindingthe(interpolated)accumulator
valueatanyhistoricaltimestampwithinthecheckpointedperiod. Inadditiontotheseconds-weightedaccumulatoroflog 1.0001 𝑝𝑟𝑖𝑐𝑒,
Uniswapv3alsotracksaseconds-weightedaccumulatorof 𝐿 1 (the
5.2 GeometricMeanPriceOracle reciprocalofthevirtualliquiditycurrentlyinrange)atthebegin-
Uniswapv2maintainstwopriceaccumulators—oneforthepriceof ningofeachblock:secondsPerLiquidityCumulative(𝑠 𝑝𝑙).
token0intermsoftoken1,andoneforthepriceoftoken1interms Thiscanbeusedbyexternalliquidityminingcontractstofairly
oftoken0.Userscancomputethetime-weightedarithmeticmean allocaterewards.Ifanexternalcontractwantstodistributerewards
ofthepricesoveranyperiod,bysubtractingtheaccumulatorvalue
atanevenrateof𝑅tokenspersecondtoallactiveliquidityinthe
atthebeginningoftheperiodfromtheaccumulatorattheendof
4Inordertosupporttolerableprecisionacrossallpossibleprices,Uniswapv2repre-
theperiod,thendividingthedifferencebythenumberofseconds
sentseachpriceasa224-bitfixed-pointnumber.Uniswapv3onlyneedstorepresent
intheperiod.Notethataccumulatorsfortoken0andtoken1are 𝑙𝑜𝑔 1.0001 𝑃asasigned24-bitnumber,andstillcandetectpricemovementsofonetick,
trackedseparately,sincethetime-weightedarithmeticmeanprice or1basispoint.
5WhilearithmeticmeanTWAPsaremuchmorewidelyused,theyshouldtheoretically
belessaccurateinmeasuringageometricBrownianmotionprocess(whichishowprice
3Themaximumof65,536checkpointsallowsfetchingcheckpointsforatleast9days movementsareusuallymodeled).ThearithmeticmeanofageometricBrownianmotion
aftertheyarewritten,assuming13secondspassbetweeneachblockandacheckpoint processwilltendtooverweighthigherprices(wheresmallpercentagemovements
iswritteneveryblock. correspondtolargeabsolutemovements)relativetolowerones.
4


## 第 5 页

Uniswapv3Core
contract,andapositionwith𝐿liquiditywasactivefrom𝑡 0to𝑡 1, Wheneverthepricecrossesaninitializedtick,virtualliquidity
thenitsrewardsforthatperiodwouldbe𝑅·L·(𝑠 𝑝𝑙(𝑡 1 )−𝑠 𝑝𝑙(𝑡 0 )). iskickedinorout.Thegascostofaninitializedtickcrossingis
Inordertoextendthissothatconcentratedliquidityisrewarded constant,andisnotdependentonthenumberofpositionsbeing
onlywhenitisinrange,Uniswapv3storesacomputedcheckpoint kickedinoroutatthattick.
basedonthisvalueeverytimeatickiscrossed,asdescribedin Ensuringthattherightamountofliquidityiskickedinandout
section6.3. ofthepoolwhenticksarecrossed,andensuringthateachposition
Thisaccumulatorcanalsobeusedbyon-chaincontractstomake earnsitsproportionalshareofthefeesthatwereaccruedwhile
theiroraclesstronger(suchasbyevaluatingwhichfee-tierpoolto it was within range, requires some accounting within the pool.
usetheoraclefrom). Thepoolcontractusesstoragevariablestotrackstateataglobal
(per-pool)level,ataper-ticklevel,andataper-positionlevel.
6 IMPLEMENTINGCONCENTRATED
6.2 GlobalState
LIQUIDITY
Theglobalstateofthecontractincludessevenstoragevariables
Therestofthispaperdescribeshowconcentratedliquidityprovi-
relevant to swaps and liquidity provision. (It has other storage
sionworks,andgivesahigh-leveldescriptionofhowitisimple-
variablesthatareusedfortheoracle,asdescribedinsection5.)
mentedinthecontracts.
Type VariableName Notation
6.1 TicksandRanges
uint128 liquidity 𝐿
√
To implement custom liquidity provision, the space of possible uint160 sqrtPriceX96 𝑃
pricesisdemarcatedbydiscreteticks.Liquidityproviderscanpro- int24 tick 𝑖 𝑐
videliquidityinarangebetweenanytwoticks(whichneednotbe uint256 feeGrowthGlobal0X128 𝑓 𝑔,0
adjacent). uint256 feeGrowthGlobal1X128 𝑓 𝑔,1
alo E w ac e h r r t a ic n k ge (𝑖 c 𝑙 a ) n an be d s a p n ec u ifi p e p d er as ti a ck pa ( i 𝑖 r 𝑢 o ). f T si i g c n k e s d r i e n p t r e e g s e e r n t t ic p k r i i n c d e i s ce a s t : u u i i n n t t 1 1 2 2 8 8 p p r r o o t t o o c c o o l l F F e e e e s s . . t t o o k k e e n n 0 1 𝑓 𝑓 𝑝 𝑝 , , 0 1
which the virtual liquidity of the contract can change. We will
Table1:GlobalState
assumethatpricesarealwaysexpressedasthepriceofoneofthe
tokens—calledtoken0—intermsoftheothertoken—token1.The
assignmentofthetwotokenstotoken0andtoken1isarbitrary
anddoesnotaffectthelogicofthecontract(otherthanthrough
6.2.1 PriceandLiquidity. InUniswapv2,eachpoolcontracttracks
possibleroundingerrors). thepool’scurrentreserves,𝑥 and𝑦.InUniswapv3,thecontract
Conceptually,thereisatickateveryprice𝑝thatisaninteger
couldbethoughtofashavingvirtualreserves—valuesfor𝑥 and𝑦
powerof1.0001.Identifyingticksbyanintegerindex𝑖,thepriceat
thatallowyoutodescribethecontract’sbehavior(betweentwo
eachisgivenby:
adjacentticks)asifitfollowedtheconstantproductformula.
Instead of tracking those virtual reserves, however, the pool
𝑝(𝑖)=1.0001 𝑖 (6.1) c √ ontracttrackstwodifferentvalues:liquidity(𝐿)andsqrtPrice
( 𝑃).Thesecouldbecomputedfromthevirtualreserveswiththe
Thishasthedesirablepropertyofeachtickbeinga.01%(1basis
followingformulas:
point)pricemovementawayfromeachofitsneighboringticks.
Fortechnicalreasonsexplainedin6.2.1,however,poolsactually √
𝐿= 𝑥𝑦 (6.3)
trackticksateverysquarerootpricethatisanintegerpowerof
√
1.0001.Considertheaboveequation,transformedintosquareroot
√ (cid:114)𝑦
pricespace: 𝑃 = (6.4)
𝑥
√ √ 𝑖 𝑖 Conversely,thesevaluescouldbeusedtocomputethevirtual
𝑝(𝑖)= 1.0001 =1.00012 (6.2) reserves:
√ √
is √ A 1 s .0 an 00 e 1 xa ≈ m 1 p .0 le 0 , 00 𝑝 5, ( a 0 n )— d t √ he 𝑝 s (− qu 1 a ) r i e s r √ oot 1 price ≈ a 0 t . t 9 i 9 ck 99 0 5 — . is1, 𝑝(1) 𝑥 = √ 𝐿 (6.5)
1.0001 𝑃
Whenliquidityisaddedtoarange,ifoneorbothoftheticks √
𝑦=𝐿· 𝑃 (6.6)
isnotalreadyusedasaboundinanexistingposition,thattickis √
initialized. Using𝐿and 𝑃isconve √ nientbecauseonlyoneofthemchanges
Noteverytickcanbeinitialized.Thepoolisinstantiatedwitha atatime.Price(andthus 𝑃)changeswhenswappingwithina
parameter,tickSpacing(𝑡 𝑠);onlytickswithindexesthataredivisi- tick;liquiditychangeswhencrossingatick,orwhenmintingor
blebytickSpacingcanbeinitialized.Forexample,iftickSpacing burningliquidity.Thisavoidssomeroundingerrorsthatcouldbe
is2,thenonlyeventicks(...-4,-2,0,2,4...)canbeinitialized.Small encounterediftrackingvirtualreserves.
choicesfortickSpacingallowtighterandmorepreciseranges,but Youmaynoticethattheformulaforliquidity(basedonvirtual
maycauseswapstobemoregas-intensive(sinceeachinitialized reserves)issimilartotheformulausedtoinitializethequantityof
tickthataswapcrossesimposesagascostontheswapper). liquiditytokens(basedonactualreserves)inUniswapv2.before
5


### 第 5 页 表格 1

| --- | --- | --- |
| Type VariableName Notation |  |  |
| uint128 | liquidity | 𝐿
√ |
| uint160 | sqrtPriceX96 | 𝑃 |
| int24 | tick | 𝑖
𝑐 |
| uint256 | feeGrowthGlobal0X128 | 𝑓
𝑔,0 |
| uint256 | feeGrowthGlobal1X128 | 𝑓
𝑔,1 |
| uint128 | protocolFees.token0 | 𝑓
𝑝,0 |
| uint128 | protocolFees.token1 | 𝑓
𝑝,1 |

## 第 6 页

HaydenAdams,NoahZinsmeister,MoodySalem,RiverKeefer,andDanRobinson
anyfeeshavebeenearned.Insomeways,liquiditycanbethought
ofasvirtualliquiditytokens. Δ𝑦=𝑦 𝑖𝑛·(1−𝛾) (6.11)
Alternatively,liquiditycanbethoughtofastheamountthat Ifyouusedthecomputedvirtualreserves(𝑥and𝑦)forthetoken0
token1reserves(eitheractualorvirtual)changesforagivenchange
√ andtoken1balances,thenthisformulacouldbeusedtofindthe
in 𝑃:
amountoftoken0sentout:
Δ𝑌
𝐿= Δ √ 𝑃 (6.7) 𝑥 𝑒𝑛𝑑 = 𝑦 𝑥 + · Δ 𝑦 𝑦 (6.12)
√
Wetrack 𝑃 insteadof𝑃 totakeadvantageofthisrelationship, Butrememberthatinv3,thecontractactuallytracksliquidity(𝐿)
√
and to avoid having to take any square roots when computing andsquarerootofprice( 𝑃)insteadof𝑥and𝑦.Wecouldcompute
swaps,asdescribedinsection6.2.3. 𝑥 and𝑦 from those values, and then use those to calculate the
Theglobalstatealsotracksthecurrenttickindexastick(𝑖 𝑐),a executionpriceofthetrade.Butitturnsoutthattherearesimple
√
signedintegerrepresentingthecurrenttick(morespecifically,the formulasthatdescribetherelationshipbetweenΔ 𝑃 andΔ𝑦,fora
nearesttickbelowthecurrentprice).Thisisanoptimization(and given𝐿(whichcanbederivedfromformula6.7):
awayofavoidingprecisionissueswithlogarithms),sinceatany
time,youshouldbeabletocomputethecurrenttickbasedonthe √ Δ𝑦
Δ 𝑃 = (6.13)
currentsqrtPrice.Specifically,atanygiventime,thefollowing 𝐿
equationshouldbetrue: √
Δ𝑦=Δ 𝑃·𝐿 (6.14)
(cid:106) √ (cid:107)
𝑖 𝑐 = log√ 1.0001 𝑃 (6.8) Therearealsosimpleformulasthatdescribetherelationship
betweenΔ√1 andΔ𝑥:
6.2.2 Fees. Eachpoolisinitializedwithanimmutablevalue,fee 𝑃
(𝛾),representingthefeepaidbyswappersinunitsofhundredths 1 Δ𝑥
ofabasispoint(0.0001%). Δ√
𝑃
=
𝐿
(6.15)
Italsotracksthecurrentprotocolfee,𝜙 (whichisinitializedto
zero,butcanchangedbyUNIgovernance).6Thisnumbergivesyou
Δ𝑥 =Δ√
1
·𝐿 (6.16)
thefractionofthefeespaidbyswappersthatcurrentlygoestothe 𝑃
protocolratherthantoliquidityproviders.𝜙 onlyhasalimitedset Whenswappingonetokenfortheother,thepoolcontractcan
√
ofpermittedvalues:0,1/4,1/5,1/6,1/7,1/8,1/9,or1/10. first compute the new 𝑃 using formula 6.13 or 6.15, and then
Theglobalstatealsotrackstwonumbers:feeGrowthGlobal0 cancomputetheamountoftoken0ortoken1tosendoutusing
(𝑓 𝑔,0)andfeeGrowthGlobal1(𝑓 𝑔,1).Theserepresentthetotalamount formula6.14or6.16. √
offeesthathavebeenearnedperunitofvirtualliquidity(𝐿),over Theseformulaswillworkforanyswapthatdoesnotpush 𝑃
√
theentirehistoryofthecontract.Youcanthinkofthemasthetotal past the price of the next initialized tick. If the computed Δ 𝑃
√
amountoffeesthatwouldhavebeenearnedby1unitofunbounded wouldcause 𝑃tomovepastthatnextinitializedtick,thecontract
liquiditythatwasdepositedwhenthecontractwasfirstinitialized.
mustonlycrossuptothattick—usinguponlypartoftheswap—and
Theyarestoredasfixed-pointunsigned128x128numbers.Note
thencrossthetick,asdescribedinsection6.3.1,beforecontinuing
thatinUniswapv3,feesarecollectedinthetokensthemselves
withtherestoftheswap.
ratherthaninliquidity,forreasonsexplainedinsection3.2.1.
Finally,theglobalstatetracksthetotalaccumulateduncollected 6.2.4 InitializedTickBitmap. Ifatickisnotusedastheendpoint
protocolfeeineachtoken,protocolFees0(𝑓 𝑝,0)andprotocolFees1 ofarangewithanyliquidityinit—thatis,ifthetickisuninitial-
(𝑓 𝑝,1).Thisisanunsigneduint128.Theaccumulatedprotocolfees ized—thenthattickcanbeskippedduringswaps.
canbecollectedbyUNIgovernance,bycallingthecollectProtocol Asanoptimizationtomakefindingthenextinitializedtickmore
function. efficient,thepooltracksabitmaptickBitmapofinitializedticks.
Thepositioninthebitmapthatcorrespondstothetickindexisset
6.2.3 SwappingWithinaSingleTick. Forsmallenoughswaps,that
to1ifthetickisinitialized,and0ifitisnotinitialized.
donotmovethepricepastatick,thecontractsactlikean𝑥·𝑦=𝑘
Whenatickisusedasanendpointforanewposition,andthat
pool.
tickisnotcurrentlyusedbyanyotherliquidity,thetickisinitialized,
Suppose𝛾 isthefee,i.e.,0.003,and𝑦 𝑖𝑛 astheamountoftoken1 andthecorrespondingbitinthebitmapissetto1.Aninitialized
sentin.
tickcanbecomeuninitializedagainifalloftheliquidityforwhich
First,feeGrowthGlobal1andprotocolFees1areincremented:
itisanendpointisremoved,inwhichcasethattick’spositionon
thebitmapiszeroedout.
Δ𝑓 𝑔,1 =𝑦 𝑖𝑛·𝛾·(1−𝜙) (6.9)
6.3 Tick-IndexedState
Δ𝑓 𝑝,1 =𝑦 𝑖𝑛·𝛾·𝜙 (6.10)
Thecontractneedstostoreinformationabouteachtickinorderto
Δ𝑦istheincreasein𝑦(afterthefeeistakenout).
tracktheamountofnetliquiditythatshouldbeaddedorremoved
6Technically,thestoragevariablecalled“protocolFee"isthedenominatorofthis whenthetickiscrossed,aswellastotrackthefeesearnedabove
fraction(oriszero,if𝜙iszero). andbelowthattick.
6


## 第 7 页

Uniswapv3Core
Start
Fail
S0. Checkinput Stop
Pass
S1. Swapwithincurrentinterval
No
S2. Isthereremaininginputoroutput? S5. Executecomputedswap
Yes
S4. Crossnexttick
Figure4:SwapControlFlow
Thecontractstoresamappingfromtickindexes(int24)tothe
(cid:40)
followingsevenvalues: 𝑓 𝑔−𝑓 𝑜(𝑖) 𝑖 𝑐 ≥𝑖
𝑓 𝑎(𝑖)= (6.17)
𝑓 𝑜(𝑖) 𝑖
𝑐
<𝑖
Type VariableName Notation
int128 liquidityNet Δ𝐿 (cid:40) 𝑓 𝑜(𝑖) 𝑖
𝑐
≥𝑖
uint128 liquidityGross 𝐿 𝑔 𝑓 𝑏(𝑖)= 𝑓 𝑔−𝑓 𝑜(𝑖) 𝑖
𝑐
<𝑖 (6.18)
uint256 feeGrowthOutside0X128 𝑓 𝑜,0
uint256 feeGrowthOutside1X128 𝑓 𝑜,1 We can use these functions to compute the total amount of
uint256 secondsOutside 𝑠 𝑜 cumulativefeespershare 𝑓 𝑟 intherangebetweentwoticks—a
uint256 tickCumulativeOutside 𝑖 𝑜 lowertick𝑖 𝑙 andanuppertick𝑖 𝑢:
uint256 secondsPerLiquidityOutsideX128 𝑠 𝑙𝑜
Table2:Tick-IndexedState 𝑓 𝑟 =𝑓 𝑔−𝑓 𝑏(𝑖 𝑙)−𝑓 𝑎(𝑖 𝑢) (6.19)
𝑓 𝑜 needstobeupdatedeachtimethetickiscrossed.Specifically,
asatick𝑖iscrossedineitherdirection,its𝑓 𝑜(foreachtoken)should
EachticktracksΔ𝐿,thetotalamountofliquiditythatshould beupdatedasfollows:
bekickedinoroutwhenthetickiscrossed.Thetickonlyneeds
totrackonesignedinteger:theamountofliquidityadded(or,if 𝑓 𝑜(𝑖):=𝑓 𝑔−𝑓 𝑜(𝑖) (6.20)
negative,removed)whenthetickiscrossedgoinglefttoright.This 𝑓 𝑜 isonlyneededforticksthatareusedaseithertheloweror
valuedoesnotneedtobeupdatedwhenthetickiscrossed(but upperboundforatleastoneposition.Asaresult,forefficiency,𝑓 𝑜is
onlywhenapositionwithaboundatthattickisupdated).
notinitialized(andthusdoesnotneedtobeupdatedwhencrossed)
Wewanttobeabletouninitializeatickwhenthereisnolonger
untilapositioniscreatedthathasthattickasoneofitsbounds.
any liquidity referencing that tick. Since Δ𝐿 is a net value, it’s When 𝑓 𝑜 is initialized for a tick𝑖, the value—by convention—is
necessarytotrackagrosstallyofliquidityreferencingthetick,
chosenasifallofthefeesearnedtodatehadoccurredbelowthat
liquidityGross.Thisvalueensuresthatevenifnetliquidityat
tick:
atickis0,wecanstillknowifatickisreferencedbyatleastone
underlyingpositionornot,whichtellsuswhethertoupdatethe (cid:40) 𝑓
𝑔
𝑖
𝑐
≥𝑖
tickbitmap. 𝑓 𝑜 := (6.21)
feeGrowthOutside{0,1}areusedtotrackhowmanyfeeswere 0 𝑖 𝑐 <𝑖
accumulatedwithinagivenrange.Sincetheformulasarethesame Notethatsince𝑓 𝑜 valuesfordifferenttickscouldbeinitialized
forthefeescollectedintoken0andtoken1,wewillomitthatsub- atdifferenttimes,comparisonsofthe𝑓 𝑜 valuesfordifferentticks
scriptfortherestofthissection. arenotmeaningful,andthereisnoguaranteethatvaluesfor 𝑓 𝑜
Youcancomputethefeesearnedperunitofliquidityintoken0 willbeconsistent.Thisdoesnotcauseaproblemforper-position
above(𝑓 𝑎)andbelow(𝑓 𝑏)atick𝑖withaformulathatdependson accounting,since,asdescribedbelow,allthepositionneedstoknow
whetherthepriceiscurrentlywithinoroutsidethatrange—thatis, isthegrowthin𝑔withinagivenrangesincethatpositionwaslast
whetherthecurrenttickindex𝑖 𝑐 isgreaterthanorequalto𝑖: touched.
7


### 第 7 页 表格 1

| --- | --- | --- |
| Type VariableName Notation |  |  |
| int128 | liquidityNet | Δ𝐿 |
| uint128 | liquidityGross | 𝐿
𝑔 |
| uint256 | feeGrowthOutside0X128 | 𝑓
𝑜,0 |
| uint256 | feeGrowthOutside1X128 | 𝑓
𝑜,1 |
| uint256 | secondsOutside | 𝑠
𝑜 |
| uint256 | tickCumulativeOutside | 𝑖
𝑜 |
| uint256 | secondsPerLiquidityOutsideX128 | 𝑠
𝑙𝑜 |

## 第 8 页

HaydenAdams,NoahZinsmeister,MoodySalem,RiverKeefer,andDanRobinson
Finally, the contract also stores secondsOutside (𝑠 𝑜),
secondsPerLiquidityOutside,andtickCumulativeOutsidefor 𝑡 𝑜 :=𝑡−𝑡 𝑜 (6.27)
eachtick.Thesevaluesarenotusedwithinthecontract,butare
Onceatickiscrossed,theswapcancontinueasdescribedin
trackedforthebenefitofexternalcontractsthatneedmorefine-
section6.2.3untilitreachesthenextinitializedtick.
grainedinformationaboutthepool’sbehavior(forpurposeslike
liquiditymining). 6.4 Position-IndexedState
Allthreeoftheseindexesworksimilarlytothefeegrowthin-
Thecontracthasamappingfromuser(anaddress),lowerbound
dexes described above. But where the feeGrowthOutside{0,1}
(atickindex,int24),andupperbound(atickindex,int24)toa
indexestrackfeeGrowthGlobal{0,1},thesecondsOutsideindex
specificPositionstruct.EachPositiontracksthreevalues:
tracks seconds (that is, the current timestamp),
secondsPerLiquidityOutside tracks the 1/𝐿 accumulator
Type VariableName Notation
(secondsPerLiquidityCumulative)describedinsection5.3,and
t
sc
i
r
c
ib
k
e
C
d
um
in
ul
s
a
e
t
c
i
ti
v
o
e
n
O
5
u
.
t
2
s
.
ide tracks the log 1.0001 𝑃 accumulator de- u
u
i
i
n
n
t
t
1
2
2
5
8
6
l
f
i
e
q
e
u
G
i
r
d
o
i
w
t
t
y
hInside0LastX128
𝑙
𝑓 𝑟,0 (𝑡 0 )
Forexample,thesecondsspentabove(𝑠 𝑎)andbelow(𝑠 𝑏)agiven uint256 feeGrowthInside1LastX128 𝑓 𝑟,1 (𝑡 0 )
tickiscomputeddifferentlybasedonwhetherthecurrentpriceis Table3:Position-IndexedState
withinthatrange,andthesecondsspentwithinarange(𝑠 𝑟)canbe
computedusingthevaluesof𝑠 𝑎and𝑠 𝑏:
liquidity(𝑙)meanstheamountofvirtualliquiditythatthe
(cid:40)
𝑡−𝑡 𝑜(𝑖) 𝑖 𝑐 ≥𝑖 positionrepresentedthelasttimethispositionwastouched.Specif-
𝑡 𝑎(𝑖)=
𝑡 𝑜(𝑖) 𝑖 𝑐 <𝑖
(6.22)
ically,liquiditycouldbethoughtofas
√
𝑥·𝑦,where𝑥 and𝑦are
therespectiveamountsofvirtualtoken0andvirtualtoken1that
(cid:40)
𝑡 𝑜(𝑖) 𝑖 𝑐 ≥𝑖 thisliquiditycontributestothepoolatanytimethatitiswithin
𝑡 𝑏(𝑖)=
𝑡−𝑡 𝑜(𝑖) 𝑖
𝑐
<𝑖
(6.23)
range.UnlikepoolsharesinUniswapv2(wherethevalueofeach
sharegrowsovertime),theunitsforliquiditydonotchangeasfees
√
𝑡 𝑟(𝑖 𝑙 ,𝑖 𝑢)=𝑡−𝑡 𝑏(𝑖 𝑙)−𝑡 𝑎(𝑖 𝑢) (6.24) areaccumulated;itisalwaysmeasuredas 𝑥·𝑦,where𝑥 and𝑦
arequantitiesoftoken0andtoken1,respectively.
Thenumberofsecondsspentwithinarangebetweentwotimes
Thisliquiditynumberdoesnotreflectthefeesthathavebeen
𝑡 1and𝑡 2canbecomputedbyrecordingthevalueof𝑠 𝑟(𝑖
𝑙
,𝑖 𝑢)at𝑡
1
accumulatedsincethecontractwaslasttouched,whichwewill
andat𝑡 2,andsubtractingtheformerfromthelatter.
call uncollected fees. Computing these uncollected fees requires
Like 𝑓 𝑜,𝑠 𝑜 doesnotneedtobetrackedforticksthatarenot
additionalstoredvaluesontheposition,feeGrowthInside0Last
ontheedgeofanyposition.Therefore,itisnotinitializeduntila
positioniscreatedthatisboundedbythattick.Byconvention,itis (𝑓 𝑟,0 (𝑡 0 )) and feeGrowthInside1Last (𝑓 𝑟,1 (𝑡 0 )), as described be-
low.
initializedasifeverysecondsincetheUnixtimestamp0hadbeen
spentbelowthattick: 6.4.1 setPosition. The setPosition function allows a liquidity
providertoupdatetheirposition.
(cid:40)
𝑡 𝑖 𝑐 ≥𝑖 TwooftheargumentstosetPosition—lowerTickandupperTick—
𝑡 𝑜(𝑖):=
0 𝑖 𝑐 <𝑖
(6.25)
whencombinedwiththemsg.sender,togetherspecifyaposition.
Thefunctiontakesoneadditionalparameter,liquidityDelta,
Aswith𝑓 𝑜 values,𝑡 𝑜 valuesarenotmeaningfullycomparable
tospecifyhowmuchvirtualliquiditytheuserwantstoaddor(if
acrossdifferentticks.𝑡 𝑜 isonlymeaningfulincomputingthenum-
negative)remove.
ber of seconds that liquidity was within some particular range First,thefunctioncomputestheuncollectedfees(𝑓 𝑢)thatthe
betweensomedefinedstarttime(whichmustbeafter𝑡 𝑜 wasini- positionisentitledto,ineachtoken.7Theamountcollectedinfees
tializedforbothticks)andsomeendtime.
iscreditedtotheuserandnettedagainsttheamountthatthey
6.3.1 CrossingaTick. Asdescribedinsection6.2.3,Uniswapv3 wouldsendinoroutfortheirvirtualliquiditydeposit.
actslikeitobeystheconstantproductformulawhenswapping To compute uncollected fees of a token, you need to know
betweeninitializedticks.Whenaswapcrossesaninitializedtick, howmuch𝑓 𝑟 fortheposition’srange(calculatedfromtherange’s
however,thecontractneedstoaddorremoveliquidity,toensure 𝑖 𝑙 and 𝑖 𝑟 as described in section 6.3) has grown since the last
thatnoliquidityproviderisinsolvent.ThismeanstheΔ𝐿isfetched timefeeswerecollectedforthatposition.Thegrowthinfeesin
fromthetick,andappliedtotheglobal𝐿. agivenrangeperunitofliquidityoverbetweentimes𝑡 0 and𝑡 1
Thecontractalsoneedstoupdatethetick’sownstate,inorder issimply𝑓 𝑟(𝑡 1 )−𝑓 𝑟(𝑡 0 )(where𝑓 𝑟(𝑡 0 )isstoredinthepositionas
totrackthefeesearned(andsecondsspent)withinrangesbounded feeGrowthInside{0,1}Last, and 𝑓 𝑟(𝑡 1 ) can be computed from
bythistick.ThefeeGrowthOutside{0,1}andsecondsOutside thecurrentstateoftheticks).Multiplyingthisbytheposition’s
valuesareupdatedtobothreflectcurrentvalues,aswellasthe liquiditygivesusthetotaluncollectedfeesintoken0forthis
properorientationrelativetothecurrenttick: position:
7Sincetheformulasforcomputinguncollectedfeesineachtokenarethesame,we
𝑓 𝑜 :=𝑓 𝑔−𝑓 𝑜 (6.26) willomitthatsubscriptfortherestofthissection.
8


### 第 8 页 表格 1

| --- | --- | --- |
| Type VariableName Notation |  |  |
| uint128 | liquidity | 𝑙 |
| uint256 | feeGrowthInside0LastX128 | 𝑓 𝑟,0 (𝑡 0 ) |
| uint256 | feeGrowthInside1LastX128 | 𝑓 𝑟,1 (𝑡 0 ) |

## 第 9 页

Uniswapv3Core
REFERENCES
𝑓 𝑢 =𝑙·(𝑓 𝑟(𝑡 1 )−𝑓 𝑟(𝑡 0 )) (6.28) [1] HaydenAdams,NoahZinsmeister,andDanRobinson.2020. Uniswapv2Core.
RetrievedFeb24,2021fromhttps://uniswap.org/whitepaper.pdf
Then,thecontractupdatestheposition’sliquiditybyadding
[2] GuillermoAngerisandTarunChitra.2020. ImprovedPriceOracles:Constant
liquidityDelta.ItalsoaddsliquidityDeltatotheliquidityNet FunctionMarketMakers.InProceedingsofthe2ndACMConferenceonAdvances
valueforthetickatthebottomendoftherange,andsubtractsit inFinancialTechnologies(AFT’20).AssociationforComputingMachinery,New
York,NY,UnitedStates,80–91. https://doi.org/10.1145/3419614.3423251
fromtheliquidityNetattheuppertick(toreflectthatthisnew
[3] MichaelEgorov.2019.StableSwap-EfficientMechanismforStablecoinLiquidity.
liquiditywouldbeaddedwhenthepricecrossesthelowertick RetrievedFeb24,2021fromhttps://www.curve.fi/stableswap-paper.pdf
goingup,andsubtractedwhenthepricecrossestheuppertick [4] AllanNiemerg,DanRobinson,andLevLivnev.2020.YieldSpace:AnAutomated
LiquidityProviderforFixedYieldTokens. RetrievedFeb24,2021fromhttps:
goingup).Ifthepool’scurrentpriceiswithintherangeofthis //yield.is/YieldSpace.pdf
position,thecontractalsoaddsliquidityDeltatothecontract’s [5] AbrahamOthman.2012.AutomatedMarketMaking:TheoryandPractice.Ph.D.
Dissertation.CarnegieMellonUniversity.
globalliquidityvalue.
Finally,thepooltransferstokensfrom(or,ifliquidityDelta
DISCLAIMER
isnegative,to)theuser,correspondingtotheamountofliquidity
burnedorminted. Thispaperisforgeneralinformationpurposesonly.Itdoesnot
Theamountoftoken0(Δ𝑋)ortoken1(Δ𝑌)thatneedstobe constituteinvestmentadviceorarecommendationorsolicitationto
depositedcanbethoughtofastheamountthatwouldbesoldfrom buyorsellanyinvestmentandshouldnotbeusedintheevaluation
thepositionifthepriceweretomovefromthecurrentprice(𝑃)to ofthemeritsofmakinganyinvestmentdecision.Itshouldnotbe
theuppertickorlowertick(fortoken0ortoken1,respectively). relieduponforaccounting,legalortaxadviceorinvestmentrec-
Theseformulascanbederivedfromformulas6.14and6.16,and ommendations.Thispaperreflectscurrentopinionsoftheauthors
dependonwhetherthecurrentpriceisbelow,within,orabovethe andisnotmadeonbehalfofUniswapLabs,Paradigm,ortheir
rangeoftheposition: affiliatesanddoesnotnecessarilyreflecttheopinionsofUniswap
Labs,Paradigm,theiraffiliatesorindividualsassociatedwiththem.
Δ𝑌 =
 0
Δ𝐿·(
√
𝑃− (cid:112)𝑝(𝑖 𝑙))
𝑖
𝑖 𝑙
𝑐
≤
<
𝑖
𝑖
𝑐
𝑙
<𝑖 𝑢 (6.29)
T
up
h
d
e
a
o
t
p
ed
in
.
ionsreflectedhereinaresubjecttochangewithoutbeing
 Δ𝐿·( (cid:112)𝑝(𝑖 𝑢)− (cid:112)𝑝(𝑖 𝑙)) 𝑖 𝑐 ≥𝑖 𝑢

Δ𝑋 =
 Δ
Δ
𝐿
𝐿
·
·
(
(
√
√1
𝑝
1
(
−
𝑖𝑙)
√
−
1
√
𝑝
1
(
)
𝑖𝑢)
) 𝑖
𝑖 𝑙
𝑐
≤
<
𝑖
𝑖
𝑐
𝑙
<𝑖 𝑢 (6.30)
0
𝑃 𝑝(𝑖𝑢)
𝑖
𝑐
≥𝑖
𝑢

9
