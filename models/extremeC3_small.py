# import os
# os.environ["CUDA_VISIBLE_DEVICES"] = "0"

import torch
import torch.nn as nn

basic_0 = 24
basic_1 = 48
basic_2 = 56
basic_3 = 24

class CBR(nn.Module):
    '''
    This class defines the convolution layer with batch normalization and PReLU activation
    '''

    def __init__(self, nIn, nOut, kSize, stride=1):
        '''

        :param nIn: number of input channels
        :param nOut: number of output channels
        :param kSize: kernel size
        :param stride: stride rate for down-sampling. Default is 1
        '''
        super().__init__()
        padding = int((kSize - 1) / 2)
        # self.conv = nn.Conv2d(nIn, nOut, kSize, stride=stride, padding=padding, bias=False)
        self.conv = nn.Conv2d(nIn, nOut, (kSize, kSize), stride=stride, padding=(padding, padding), bias=False)
        # self.conv1 = nn.Conv2d(nOut, nOut, (1, kSize), stride=1, padding=(0, padding), bias=False)
        self.bn = nn.BatchNorm2d(nOut, eps=1e-03)
        self.act = nn.PReLU(nOut)
        # self.act = nn.ReLU()


    def forward(self, input):
        '''
        :param input: input feature map
        :return: transformed feature map
        '''
        output = self.conv(input)
        # output = self.conv1(output)
        output = self.bn(output)
        output = self.act(output)
        return output


class BR(nn.Module):
    '''
        This class groups the batch normalization and PReLU activation
    '''

    def __init__(self, nOut):
        '''
        :param nOut: output feature maps
        '''
        super().__init__()
        self.bn = nn.BatchNorm2d(nOut, eps=1e-03)
        self.act = nn.PReLU(nOut)
        # self.act = nn.ReLU()

    def forward(self, input):
        '''
        :param input: input feature map
        :return: normalized and thresholded feature map
        '''
        output = self.bn(input)
        output = self.act(output)
        return output


class CB(nn.Module):
    '''
       This class groups the convolution and batch normalization
    '''

    def __init__(self, nIn, nOut, kSize, stride=1):
        '''
        :param nIn: number of input channels
        :param nOut: number of output channels
        :param kSize: kernel size
        :param stride: optinal stide for down-sampling
        '''
        super().__init__()
        padding = int((kSize - 1) / 2)
        self.conv = nn.Conv2d(nIn, nOut, (kSize, kSize), stride=stride, padding=(padding, padding), bias=False)
        self.bn = nn.BatchNorm2d(nOut, eps=1e-03)

    def forward(self, input):
        '''

        :param input: input feature map
        :return: transformed feature map
        '''
        output = self.conv(input)
        output = self.bn(output)
        return output


class C(nn.Module):
    '''
    This class is for a convolutional layer.
    '''

    def __init__(self, nIn, nOut, kSize, stride=1):
        '''

        :param nIn: number of input channels
        :param nOut: number of output channels
        :param kSize: kernel size
        :param stride: optional stride rate for down-sampling
        '''
        super().__init__()
        padding = int((kSize - 1) / 2)
        self.conv = nn.Conv2d(nIn, nOut, (kSize, kSize), stride=stride, padding=(padding, padding), bias=False)

    def forward(self, input):
        '''
        :param input: input feature map
        :return: transformed feature map
        '''
        output = self.conv(input)
        return output



class C3_block(nn.Module):
    '''
    This class defines the dilated convolution.
    '''

    def __init__(self, nIn, nOut, kSize, stride=1, d=1):
        '''
        :param nIn: number of input channels
        :param nOut: number of output channels
        :param kSize: kernel size
        :param stride: optional stride rate for down-sampling
        :param d: optional dilation rate
        '''
        super().__init__()
        padding = int((kSize - 1) / 2) * d
        if d == 1:
            self.conv =nn.Sequential(
                nn.Conv2d(nIn, nIn, (kSize, kSize), stride=stride, padding=(padding, padding), groups=nIn, bias=False,
                          dilation=d),
                nn.Conv2d(nIn, nOut, kernel_size=1, stride=1, bias=False)
            )
        else:
            combine_kernel = 2 * d - 1

            self.conv = nn.Sequential(
                nn.Conv2d(nIn, nIn, kernel_size=(combine_kernel, 1), stride=stride, padding=(padding - 1, 0),
                          groups=nIn, bias=False),
                nn.BatchNorm2d(nIn),
                nn.PReLU(nIn),
                nn.Conv2d(nIn, nIn, kernel_size=(1, combine_kernel), stride=stride, padding=(0, padding - 1),
                          groups=nIn, bias=False),
                nn.BatchNorm2d(nIn),
                nn.Conv2d(nIn, nIn, (kSize, kSize), stride=stride, padding=(padding, padding), groups=nIn, bias=False,
                          dilation=d),
                nn.Conv2d(nIn, nOut, kernel_size=1, stride=1, bias=False))

    def forward(self, input):
        '''
        :param input: input feature map
        :return: transformed feature map
        '''
        output = self.conv(input)
        return output


class Down_C3module(nn.Module):
    def __init__(self, nIn, nOut, ratio=[2,4,8]):
        super().__init__()
        n = int(nOut // 3)
        n1 = nOut - 3 * n
        self.c1 = C(nIn, n, 3, 2)
        # self.d1 = Double_CDilated(n, n1, 3, 1, 1)
        self.d1 = C3_block(n, n+n1, 3, 1, ratio[0])
        self.d2 = C3_block(n, n, 3, 1, ratio[1])
        self.d3 = C3_block(n, n, 3, 1, ratio[2])
        # self.conv =C(nOut, nOut, 1,1)
        self.bn = nn.BatchNorm2d(nOut, eps=1e-3)
        self.act = nn.PReLU(nOut)

    def forward(self, input):
        output1 = self.c1(input)
        d1 = self.d1(output1)
        d2 = self.d2(output1)
        d3 = self.d3(output1)
        # d4 = self.d4(output1)

        # add1 = d2
        # add2 = d2 + d4
        # add3 = d4 + d8
        # add4 = d8 + d16

        # combine = torch.cat([add1, add2, add3, add4], 1)
        combine = torch.cat([d1, d2, d3], 1)
        # combine= self.conv(combine)
        # combine_in_out = input + combine
        output = self.bn(combine)
        output = self.act(output)
        return output

class C3module(nn.Module):
    '''
    This class defines the ESP block, which is based on the following principle
        Reduce ---> Split ---> Transform --> Merge
    '''

    def __init__(self, nIn, nOut, add=True, ratio=[2,4,8]):
        '''
        :param nIn: number of input channels
        :param nOut: number of output channels
        :param add: if true, add a residual connection through identity operation. You can use projection too as
                in ResNet paper, but we avoid to use it if the dimensions are not the same because we do not want to
                increase the module complexity
        '''
        super().__init__()
        n = int(nOut // 3)
        n1 = nOut - 3 * n
        self.c1 = C(nIn, n, 1, 1)

        self.d1 = C3_block(n, n + n1, 3, 1, ratio[0])
        self.d2 = C3_block(n, n, 3, 1, ratio[1])
        self.d3 = C3_block(n, n, 3, 1, ratio[2])
        # self.d4 = Double_CDilated(n, n, 3, 1, 12)
        # self.conv =C(nOut, nOut, 1,1)

        self.bn = BR(nOut)
        self.add = add

    def forward(self, input):
        '''
        :param input: input feature map
        :return: transformed feature map
        '''
        # reduce
        output1 = self.c1(input)
        d1 = self.d1(output1)
        d2 = self.d2(output1)
        d3 = self.d3(output1)

        combine = torch.cat([d1, d2, d3], 1)

        if self.add:
            combine = input + combine
        output = self.bn(combine)
        return output


class InputProjectionA(nn.Module):
    '''
    This class projects the input image to the same spatial dimensions as the feature map.
    For example, if the input image is 512 x512 x3 and spatial dimensions of feature map size are 56x56xF, then
    this class will generate an output of 56x56x3
    '''

    def __init__(self, samplingTimes):
        '''
        :param samplingTimes: The rate at which you want to down-sample the image
        '''
        super().__init__()
        self.pool = nn.ModuleList()
        for i in range(0, samplingTimes):
            # pyramid-based approach for down-sampling
            self.pool.append(nn.AvgPool2d(2, stride=2, padding=0))

    def forward(self, input):
        '''
        :param input: Input RGB Image
        :return: down-sampled image (pyramid-based approach)
        '''
        for pool in self.pool:
            input = pool(input)
        return input


class ExtremeC3Net(nn.Module):
    '''
    This class defines the ESPNet-C network in the paper
    '''

    def __init__(self, classes=20, p=5, q=3,stage2=False):
        '''
        :param classes: number of classes in the dataset. Default is 20 for the cityscapes
        :param p: depth multiplier
        :param q: depth multiplier
        '''
        super().__init__()

        self.level1 = CBR(3, basic_0, 3, 2)
        self.sample1 = InputProjectionA(1)
        self.sample2 = InputProjectionA(2)

        self.b1 = BR(basic_0 + 3)
        self.level2_0 = Down_C3module(basic_0 + 3, basic_1, ratio=[1, 2, 3])  # , ratio=[1,2,3]

        self.level2 = nn.ModuleList()
        for i in range(0, p):
            self.level2.append(
                C3module(basic_1, basic_1, ratio=[1, 3, 4]))  # , ratio=[1,3,4]
        self.b2 = BR(basic_1 * 2 + 3)

        # self.level3_0 = Double_DownSamplerB(basic_1*2 + 3, basic_2, ratio=[1,3,5])
        self.level3_0 = C3module(basic_1 * 2 + 3, basic_2, add=False,
                                                            ratio=[1, 3, 5])  # , ratio=[1,3,5]

        self.level3 = nn.ModuleList()
        for i in range(0, q):
            self.level3.append(C3module(basic_2, basic_2))
        self.b3 = BR(basic_2 * 2)

        if stage2:
            self.upsample = nn.Sequential(
                nn.Conv2d(kernel_size=(1, 1), in_channels=basic_2*2, out_channels=basic_3,bias=False),

                nn.UpsamplingBilinear2d(scale_factor=4),
                nn.BatchNorm2d(basic_3, eps=1e-03),
                nn.PReLU(basic_3),

            )
        else:
            self.upsample = nn.Sequential(
                nn.Conv2d(kernel_size=(1, 1), in_channels=basic_2 * 2, out_channels=basic_3, bias=False),
                nn.BatchNorm2d(basic_3, eps=1e-03),
                nn.PReLU(basic_3),

            )

        self.classifier = nn.Sequential(
            nn.Conv2d(kernel_size=(1, 1), in_channels=basic_3, out_channels=classes, bias=False)
        )


    def forward(self, input):
        '''
        :param input: Receives the input RGB image
        :return: the transformed feature map with spatial dimensions 1/8th of the input image
        '''
        output0 = self.level1(input)
        inp1 = self.sample1(input)
        inp2 = self.sample2(input)

        output0_cat = self.b1(torch.cat([output0, inp1], 1))
        output1_0 = self.level2_0(output0_cat)  # down-sampled

        for i, layer in enumerate(self.level2):
            if i == 0:
                output1 = layer(output1_0)
            else:
                output1 = layer(output1)

        output1_cat = self.b2(torch.cat([output1, output1_0, inp2], 1))

        output2_0 = self.level3_0(output1_cat)  # down-sampled
        for i, layer in enumerate(self.level3):
            if i == 0:
                output2 = layer(output2_0)
            else:
                output2 = layer(output2)

        output2_cat = self.b3(torch.cat([output2_0, output2], 1))

        Coarse = self.upsample(output2_cat)
        # Fine =  self.Fine(input)
        classifier = self.classifier(Coarse)
        return classifier



def ExtremeC3Net_small(classes=2, p=1, q=5,stage2=False, enc_file=None):
    if not stage2:
        print("train small version")
        model = ExtremeC3Net(classes=classes, p=p, q=q,stage2=stage2)
    else:
        model = ExtremeC3Net(classes=classes, p=p, q=q,stage2=stage2)
        if enc_file != None:
            pretrained_dict = torch.load(enc_file)

            state_dict = model.state_dict()
            overlap_dict = {k: v for k, v in pretrained_dict.items() if k in state_dict}
            state_dict.update(overlap_dict)
            if len(overlap_dict) == 0:
                print('No overlaping weights between model file and pretrained weight file. Please check')
            else:
                print('{:.2f} % of weights copied from basenet to segnet'.
                      format(len(overlap_dict) * 1.0 / len(state_dict) * 100))

            model.load_state_dict(state_dict)
            print('Pretrained basenet model loaded!!')
    return model



if __name__ == '__main__':
    import time
    import torch
    from etc.flops_counter import add_flops_counting_methods, flops_to_string, get_model_parameters_number
    from etc.flops_compute import compute_flops
    # model = C3_ESPNet_Encoder(classes=2, p=1, q=5)
    model = ExtremeC3Net_small(classes=1, p=1, q=5, stage2=True)
    batch = torch.FloatTensor(1, 3, 224, 224)

    model_eval = add_flops_counting_methods(model)
    model_eval.eval().start_flops_count()
    out = model_eval(batch)  # ,only_encode=True)

    print('Flops:  {}'.format(flops_to_string(model.compute_average_flops_cost())))
    print('Params: ' + get_model_parameters_number(model))
    print('Output shape: {}'.format(list(out.shape)))
    total_paramters = sum(p.numel() for p in model.parameters())
    print(total_paramters)

    # flops = compute_flops(model, input=torch.Tensor(1, 3, 224, 224))
    # print('non use deconv Flops: ' + str(flops))
    #
    #
    # model.eval()
    #
    # images = torch.randn(1,3,224,224)
    # batch_size=1
    # # if torch.cuda.is_available():
    # #     model = model.cuda()  # .half()	#HALF seems to be doing slower for some reason
    # #     images = images.cuda()  # .half()
    #
    # time_train = []
    # i = 0
    # # model.load_state_dict(torch.load("../Testmodel_List/KR94187_Portrait_98/result/Dnc_C3Portrait/model_266.pth",
    # #                       map_location=torch.device(device='cpu')))
    #
    # while (i < 50):
    #     # for step, (images, labels, filename, filenameGt) in enumerate(loader):
    #
    #     start_time = time.time()
    #
    #     inputs = torch.autograd.Variable(images)
    #     with torch.no_grad():
    #         outputs = model(inputs)
    #
    #     # preds = outputs.cpu()
    #     # if torch.cuda.is_available():
    #     #     torch.cuda.synchronize()  # wait for cuda to finish (cuda is asynchronous!)
    #
    #     if i != 0:  # first run always takes some time for setup
    #         fwt = time.time() - start_time
    #         time_train.append(fwt)
    #         print("Forward time per img (b=%d): %.3f (Mean: %.3f)" % (
    #            batch_size, fwt / batch_size, sum(time_train) / len(time_train) /batch_size))
    #
    #     time.sleep(1)  # to avoid overheating the GPU too much
    #     i += 1
    #
    #
    #
