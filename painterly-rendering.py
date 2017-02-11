from time import time
import logging
import argparse
import painterly

t1 = time()

q_radii = {
    'low': [64, 32, 16, 8],
    'medium': [64, 16, 8, 4],
    'high': [64, 8, 4, 2]}

if __name__ == '__main__':
    
    # parse input arguments
    parser = argparse.ArgumentParser(description='Apply painterly rendering to an image.')
    parser.add_argument('-q', dest='quality', default='medium', choices=['low', 'medium', 'high'],
                        help='Sets the size of the brush radius when painting.')
    parser.add_argument('-i', dest='in_filename', required=True,
                        help='The path of the input file.')
    parser.add_argument('-o', dest='out_filename', default=None,
                        help='The name of the output file.')
    parser.add_argument('-l', dest='save_layers', action='store_true',
                        help='Outputs an intermediary image when each layer of detail is completed.')
    parser.add_argument('-v', dest='verbose', action='store_true',
                        help='Allows more verbose output to give the user more feedback.')
    
    args = parser.parse_args()
    
    
    # set log level
    if args.verbose:
        logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
    else:
        logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.WARNING)
    
    # set brush radii
    radii = q_radii[args.quality]
    
    # load and convert input image to RGB
    logging.info("Generating new painting...")
    logging.info("\tOpening image...")
    newPainting = painterly.Painting(args.in_filename)
    logging.info("\t\tdone.")
    
    # render the image
    newPainting.render(radii=radii, save_layers=args.save_layers)
    
    # save the output image
    if args.out_filename:
        newPainting.save(filepath=args.out_filename)
    else:
        newPainting.save()
        
    
    logging.info("done")
    logging.info("Time: " + "{0:.2f}".format(time()-t1) + " seconds.")
